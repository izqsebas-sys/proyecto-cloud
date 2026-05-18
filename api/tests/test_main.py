import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import _config_cache, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache(monkeypatch):
    _config_cache.clear()
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("RABBITMQ_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "test")
    monkeypatch.setenv("DB_PASSWORD", "test")


def make_mock_conn(fetchone_return=None, fetchall_return=None):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return
    mock_cur.fetchall.return_value = fetchall_return or []
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


def make_mock_rabbitmq():
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    return mock_conn, mock_channel


# --- Health Check ---

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# --- POST /orders ---

def test_create_order_returns_202():
    mock_conn, _ = make_mock_conn()
    rmq_conn, rmq_channel = make_mock_rabbitmq()

    with patch("main.get_db_connection", return_value=mock_conn), \
         patch("main.get_rabbitmq_channel", return_value=(rmq_conn, rmq_channel)):

        response = client.post(
            "/orders",
            json={"description": "Test order", "quantity": 2, "product": "Widget"},
        )

    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_create_order_inserts_task_and_publishes():
    mock_conn, mock_cur = make_mock_conn()
    rmq_conn, rmq_channel = make_mock_rabbitmq()

    with patch("main.get_db_connection", return_value=mock_conn), \
         patch("main.get_rabbitmq_channel", return_value=(rmq_conn, rmq_channel)):

        client.post(
            "/orders",
            json={"description": "Test", "quantity": 1, "product": "Gadget"},
        )

    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    rmq_channel.basic_publish.assert_called_once()


def test_create_order_db_error_returns_500():
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.execute.side_effect = Exception("DB down")

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.post(
            "/orders",
            json={"description": "Test", "quantity": 1, "product": "Widget"},
        )

    assert response.status_code == 500


# --- GET /tasks/{task_id} ---

def test_get_task_found():
    task_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    now = datetime.now(timezone.utc)
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(task_id, "pending", now, now))

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "pending"


def test_get_task_not_found():
    mock_conn, _ = make_mock_conn(fetchone_return=None)

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get("/tasks/nonexistent-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_get_task_db_error_returns_500():
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.execute.side_effect = Exception("DB down")

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get("/tasks/some-id")

    assert response.status_code == 500


# --- GET /orders ---

def test_get_orders_empty():
    mock_conn, _ = make_mock_conn(fetchall_return=[])

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get("/orders")

    assert response.status_code == 200
    assert response.json() == []


def test_get_orders_with_data():
    now = datetime.now(timezone.utc)
    mock_conn, _ = make_mock_conn(
        fetchall_return=[
            ("order-1", "task-1", {"product": "Widget"}, now),
            ("order-2", "task-2", {"product": "Gadget"}, now),
        ]
    )

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get("/orders")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["order_id"] == "order-1"


# --- PUT /orders/{order_id} ---

def test_update_order_success():
    order_id = "order-123"
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(order_id,))

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.put(
            f"/orders/{order_id}",
            json={"description": "Updated description", "quantity": 5},
        )

    assert response.status_code == 200
    assert response.json()["order_id"] == order_id
    assert response.json()["status"] == "updated"


def test_update_order_not_found():
    mock_conn, _ = make_mock_conn(fetchone_return=None)

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.put(
            "/orders/nonexistent",
            json={"description": "test"},
        )

    assert response.status_code == 404


# --- DELETE /orders/{order_id} ---

def test_delete_order_returns_202():
    order_id = "order-to-delete"
    mock_conn_check, _ = make_mock_conn(fetchone_return=(order_id,))
    mock_conn_task, _ = make_mock_conn()
    rmq_conn, rmq_channel = make_mock_rabbitmq()

    call_count = {"n": 0}

    def side_effect_db():
        call_count["n"] += 1
        return mock_conn_check if call_count["n"] == 1 else mock_conn_task

    with patch("main.get_db_connection", side_effect=side_effect_db), \
         patch("main.get_rabbitmq_channel", return_value=(rmq_conn, rmq_channel)):

        response = client.delete(f"/orders/{order_id}")

    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_delete_order_not_found():
    mock_conn, _ = make_mock_conn(fetchone_return=None)

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.delete("/orders/nonexistent")

    assert response.status_code == 404
