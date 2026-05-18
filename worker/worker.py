import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone

import boto3
import pika
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_config_cache: dict = {}


def get_ssm_parameter(name: str, retries: int = 15, delay: int = 15) -> str:
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


def update_task_status(task_id: str, status: str) -> None:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc)
        cur.execute(
            "UPDATE tasks SET status = %s, updated_at = %s WHERE task_id = %s",
            (status, now, task_id),
        )
        conn.commit()
        cur.close()
        logger.info(f"Tarea {task_id} actualizada a estado={status}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al actualizar tarea {task_id}: {e}")
        raise
    finally:
        conn.close()


def handle_create(ch, method, properties, body):
    try:
        message = json.loads(body)
        task_id = message["task_id"]
        payload = message["payload"]

        logger.info(f"Procesando creación para task_id={task_id}")

        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO orders (order_id, task_id, payload, created_at) VALUES (%s, %s, %s::jsonb, %s)",
                (order_id, task_id, json.dumps(payload), now),
            )
            conn.commit()
            cur.close()
            logger.info(f"Pedido {order_id} creado para task_id={task_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear pedido: {e}")
            raise
        finally:
            conn.close()

        update_task_status(task_id, "completado")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error procesando mensaje de creación: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def handle_delete(ch, method, properties, body):
    try:
        message = json.loads(body)
        task_id = message["task_id"]
        order_id = message["order_id"]

        logger.info(f"Procesando eliminación para pedido_id={order_id}, task_id={task_id}")

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
            conn.commit()
            cur.close()
            logger.info(f"Pedido {order_id} eliminado")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar pedido {order_id}: {e}")
            raise
        finally:
            conn.close()

        update_task_status(task_id, "completado")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error procesando mensaje de eliminación: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def consume_queue(queue: str, callback, rabbitmq_host: str) -> None:
    while True:
        try:
            credentials = pika.PlainCredentials(
                os.environ.get("RABBITMQ_USER", "user"),
                os.environ.get("RABBITMQ_PASSWORD", "password"),
            )
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
            )
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue, on_message_callback=callback)
            logger.info(f"Consumiendo cola: {queue}")
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Worker para cola {queue} falló: {e}. Reconectando en 10s...")
            time.sleep(10)


def main():
    logger.info("Iniciando worker...")
    rabbitmq_host = get_rabbitmq_host()
    logger.info(f"Host RabbitMQ: {rabbitmq_host}")

    create_thread = threading.Thread(
        target=consume_queue,
        args=("orders_create", handle_create, rabbitmq_host),
        daemon=True,
    )
    delete_thread = threading.Thread(
        target=consume_queue,
        args=("orders_delete", handle_delete, rabbitmq_host),
        daemon=True,
    )

    create_thread.start()
    delete_thread.start()

    logger.info("Hilos del worker iniciados. Esperando mensajes...")
    create_thread.join()
    delete_thread.join()


if __name__ == "__main__":
    main()
