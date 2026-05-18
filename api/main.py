import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import boto3
import pika
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(
    title="API de Pedidos Asíncronos",
    description="API de procesamiento asíncrono de pedidos con RabbitMQ y PostgreSQL",
    version="1.0.0",
)


def _validar_uuid(valor: str, nombre: str = "ID") -> None:
    try:
        uuid.UUID(valor)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"{nombre} no encontrado")

_config_cache: dict = {}


def get_ssm_parameter(name: str, retries: int = 10, delay: int = 15) -> str:
    ssm = boto3.client("ssm", region_name="us-east-1")
    for attempt in range(retries):
        try:
            response = ssm.get_parameter(Name=name)
            return response["Parameter"]["Value"]
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f"Parámetro SSM {name} no disponible, reintentando en {delay}s... ({e})")
                time.sleep(delay)
            else:
                raise


def get_config(key: str, env_var: str, ssm_name: str) -> str:
    if key not in _config_cache:
        value = os.environ.get(env_var)
        if not value:
            value = get_ssm_parameter(ssm_name)
        _config_cache[key] = value
    return _config_cache[key]


def get_postgres_host() -> str:
    return get_config("postgres_host", "POSTGRES_HOST", "/proyecto/postgres_host")


def get_rabbitmq_host() -> str:
    return get_config("rabbitmq_host", "RABBITMQ_HOST", "/proyecto/rabbitmq_host")


def get_db_connection():
    return psycopg2.connect(
        host=get_postgres_host(),
        database=os.environ.get("DB_NAME", "ordersdb"),
        user=os.environ.get("DB_USER", "appuser"),
        password=os.environ.get("DB_PASSWORD", "apppassword"),
        port=int(os.environ.get("DB_PORT", "5432")),
    )


def get_rabbitmq_channel():
    credentials = pika.PlainCredentials(
        os.environ.get("RABBITMQ_USER", "user"),
        os.environ.get("RABBITMQ_PASSWORD", "password"),
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=get_rabbitmq_host(), credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue="orders_create", durable=True)
    channel.queue_declare(queue="orders_delete", durable=True)
    return connection, channel


def publish_message(queue: str, message: dict) -> None:
    connection, channel = get_rabbitmq_channel()
    try:
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        connection.close()


class OrderCreate(BaseModel):
    description: str
    quantity: int
    product: str


class OrderUpdate(BaseModel):
    description: Optional[str] = None
    quantity: Optional[int] = None
    product: Optional[str] = None


@app.get("/health")
def health_check():
    return {"estado": "saludable"}


@app.post("/orders", status_code=202)
def create_order(order: OrderCreate):
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (task_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s)",
            (task_id, "pendiente", now, now),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error de BD al crear tarea: {e}")
        raise HTTPException(status_code=500, detail="Error al crear la tarea")
    finally:
        conn.close()

    try:
        publish_message("orders_create", {"task_id": task_id, "payload": order.model_dump()})
    except Exception as e:
        logger.error(f"Error de RabbitMQ: {e}")
        raise HTTPException(status_code=500, detail="Error al encolar el pedido")

    logger.info(f"Pedido encolado con task_id={task_id}")
    return {"task_id": task_id, "estado": "pendiente"}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    _validar_uuid(task_id, "Tarea")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT task_id, status, created_at, updated_at FROM tasks WHERE task_id = %s",
            (task_id,),
        )
        row = cur.fetchone()
        cur.close()
    except Exception as e:
        logger.error(f"Error de BD al obtener tarea: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener la tarea")
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    return {
        "task_id": str(row[0]),
        "estado": row[1],
        "creado_en": str(row[2]),
        "actualizado_en": str(row[3]),
    }


@app.get("/orders")
def get_orders():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT order_id, task_id, payload, created_at FROM orders ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        cur.close()
    except Exception as e:
        logger.error(f"Error de BD al obtener pedidos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener los pedidos")
    finally:
        conn.close()

    return [
        {
            "pedido_id": str(r[0]),
            "task_id": str(r[1]),
            "datos": r[2],
            "creado_en": str(r[3]),
        }
        for r in rows
    ]


@app.put("/orders/{order_id}")
def update_order(order_id: str, order: OrderUpdate):
    _validar_uuid(order_id, "Pedido")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT order_id FROM orders WHERE order_id = %s", (order_id,))
        if not cur.fetchone():
            cur.close()
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        updates = {k: v for k, v in order.model_dump().items() if v is not None}
        if updates:
            cur.execute(
                "UPDATE orders SET payload = payload || %s::jsonb WHERE order_id = %s",
                (json.dumps(updates), order_id),
            )
        conn.commit()
        cur.close()
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error de BD al actualizar pedido: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el pedido")
    finally:
        conn.close()

    logger.info(f"Pedido {order_id} actualizado de forma síncrona")
    return {"pedido_id": order_id, "estado": "actualizado"}


@app.delete("/orders/{order_id}", status_code=202)
def delete_order(order_id: str):
    _validar_uuid(order_id, "Pedido")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT order_id FROM orders WHERE order_id = %s", (order_id,))
        if not cur.fetchone():
            cur.close()
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        cur.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error de BD al verificar pedido: {e}")
        raise HTTPException(status_code=500, detail="Error al verificar el pedido")
    finally:
        conn.close()

    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (task_id, status, created_at, updated_at) VALUES (%s, %s, %s, %s)",
            (task_id, "pendiente", now, now),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error de BD al crear tarea de eliminación: {e}")
        raise HTTPException(status_code=500, detail="Error al crear la tarea")
    finally:
        conn.close()

    try:
        publish_message("orders_delete", {"task_id": task_id, "order_id": order_id})
    except Exception as e:
        logger.error(f"Error de RabbitMQ: {e}")
        raise HTTPException(status_code=500, detail="Error al encolar la eliminación")

    logger.info(f"Eliminación encolada para pedido={order_id}, task_id={task_id}")
    return {"task_id": task_id, "estado": "pendiente"}
