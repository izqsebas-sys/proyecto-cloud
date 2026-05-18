import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import _config_cache, app

client = TestClient(app)

VALID_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
INVALID_ID = "id-invalido"


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
    assert response.json() == {"estado": "saludable"}


# --- POST /orders ---

def test_create_order_returns_202():
    mock_conn, _ = make_mock_conn()
    rmq_conn, rmq_channel = make_mock_rabbitmq()

    with patch("main.get_db_connection", return_value=mock_conn), \
         patch("main.get_rabbitmq_channel", return_value=(rmq_conn, rmq_channel)):

        response = client.post(
            "/orders",
            json={"description": "Pedido de prueba", "quantity": 2, "product": "Widget"},
        )

    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["estado"] == "pendiente"


def test_create_order_inserts_task_and_publishes():
    mock_conn, mock_cur = make_mock_conn()
    rmq_conn, rmq_channel = make_mock_rabbitmq()

    with patch("main.get_db_connection", return_value=mock_conn), \
         patch("main.get_rabbitmq_channel", return_value=(rmq_conn, rmq_channel)):

        client.post(
            "/orders",
            json={"description": "Prueba", "quantity": 1, "product": "Gadget"},
        )

    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    rmq_channel.basic_publish.assert_called_once()


def test_create_order_db_error_returns_500():
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.execute.side_effect = Exception("BD caída")

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.post(
            "/orders",
            json={"description": "Prueba", "quantity": 1, "product": "Widget"},
        )

    assert response.status_code == 500


# --- GET /tasks/{task_id} ---

def test_get_task_found():
    now = datetime.now(timezone.utc)
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(VALID_UUID, "pendiente", now, now))

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get(f"/tasks/{VALID_UUID}")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == VALID_UUID
    assert data["estado"] == "pendiente"


def test_get_task_not_found():
    mock_conn, _ = make_mock_conn(fetchone_return=None)

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get(f"/tasks/{VALID_UUID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Tarea no encontrada"


def test_get_task_invalid_uuid_message():
    response = client.get(f"/tasks/{INVALID_ID}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarea no encontrada"


def test_get_task_invalid_uuid_returns_404():
    response = client.get(f"/tasks/{INVALID_ID}")
    assert response.status_code == 404


def test_get_task_db_error_returns_500():
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.execute.side_effect = Exception("BD caída")

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get(f"/tasks/{VALID_UUID}")

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
            ("pedido-1", "task-1", {"producto": "Widget"}, now),
            ("pedido-2", "task-2", {"producto": "Gadget"}, now),
        ]
    )

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.get("/orders")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["pedido_id"] == "pedido-1"


# --- PUT /orders/{order_id} ---

def test_update_order_success():
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(VALID_UUID,))

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.put(
            f"/orders/{VALID_UUID}",
            json={"description": "Descripción actualizada", "quantity": 5},
        )

    assert response.status_code == 200
    assert response.json()["pedido_id"] == VALID_UUID
    assert response.json()["estado"] == "actualizado"


def test_update_order_not_found():
    mock_conn, _ = make_mock_conn(fetchone_return=None)

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.put(
            f"/orders/{VALID_UUID}",
            json={"description": "prueba"},
        )

    assert response.status_code == 404


def test_update_order_invalid_uuid_returns_404():
    response = client.put(f"/orders/{INVALID_ID}", json={"description": "prueba"})
    assert response.status_code == 404


# --- DELETE /orders/{order_id} ---

def test_delete_order_returns_202():
    mock_conn_check, _ = make_mock_conn(fetchone_return=(VALID_UUID,))
    mock_conn_task, _ = make_mock_conn()
    rmq_conn, rmq_channel = make_mock_rabbitmq()

    call_count = {"n": 0}

    def side_effect_db():
        call_count["n"] += 1
        return mock_conn_check if call_count["n"] == 1 else mock_conn_task

    with patch("main.get_db_connection", side_effect=side_effect_db), \
         patch("main.get_rabbitmq_channel", return_value=(rmq_conn, rmq_channel)):

        response = client.delete(f"/orders/{VALID_UUID}")

    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["estado"] == "pendiente"


def test_delete_order_not_found():
    mock_conn, _ = make_mock_conn(fetchone_return=None)

    with patch("main.get_db_connection", return_value=mock_conn):
        response = client.delete(f"/orders/{VALID_UUID}")

    assert response.status_code == 404


def test_delete_order_invalid_uuid_returns_404():
    response = client.delete(f"/orders/{INVALID_ID}")
    assert response.status_code == 404
