# =============================================================================
# Worker — Procesador de Mensajes de RabbitMQ
# =============================================================================
# Este archivo es el "trabajador" del sistema. Corre en su propia instancia EC2
# y se encarga de consumir los mensajes de las colas de RabbitMQ para:
#   1. Crear pedidos en PostgreSQL (cola: orders_create)
#   2. Eliminar pedidos de PostgreSQL (cola: orders_delete)
#
# El Worker corre indefinidamente escuchando mensajes. Usa dos hilos (threads)
# para procesar creaciones y eliminaciones al mismo tiempo.
# =============================================================================

import json
import logging
import os
import threading   # Para correr dos consumidores de cola en paralelo
import time
import uuid
from datetime import datetime, timezone

import boto3       # SDK de AWS para leer parámetros de SSM
import pika        # Librería para conectarse a RabbitMQ
import psycopg2    # Conector para PostgreSQL

# Configuramos logs con timestamp para facilitar la depuración en producción
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Caché en memoria para no consultar SSM en cada mensaje procesado
_config_cache: dict = {}


# =============================================================================
# Funciones de configuración — igual que en la API, lee IPs desde SSM
# =============================================================================

def get_ssm_parameter(name: str, retries: int = 15, delay: int = 15) -> str:
    """Obtiene un parámetro de SSM con más reintentos que la API (15 vs 10)
    porque el Worker arranca al mismo tiempo que las demás instancias y
    puede necesitar más tiempo para que SSM tenga los valores listos."""
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
    """Busca primero en variables de entorno, luego en SSM."""
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
    """Abre una conexión fresca a PostgreSQL.
    Abrimos y cerramos la conexión por cada mensaje para evitar timeouts en conexiones largas."""
    return psycopg2.connect(
        host=get_postgres_host(),
        database=os.environ.get("DB_NAME", "ordersdb"),
        user=os.environ.get("DB_USER", "appuser"),
        password=os.environ.get("DB_PASSWORD", "apppassword"),
        port=int(os.environ.get("DB_PORT", "5432")),
    )


# =============================================================================
# Función auxiliar para actualizar el estado de una tarea
# =============================================================================

def update_task_status(task_id: str, status: str) -> None:
    """Actualiza el campo 'status' de una tarea en PostgreSQL.
    Se llama al final de handle_create y handle_delete para marcar la operación como completada."""
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


# =============================================================================
# Manejadores de mensajes — uno por tipo de operación
# =============================================================================

def handle_create(ch, method, properties, body):
    """Procesa un mensaje de la cola 'orders_create'.

    Pasos:
    1. Deserializa el mensaje JSON
    2. Inserta el pedido en la tabla 'orders' de PostgreSQL
    3. Actualiza la tarea a 'completado'
    4. Confirma el mensaje a RabbitMQ (basic_ack) para que no lo reenvíe

    Si algo falla, hace basic_nack con requeue=False para descartar el mensaje
    y evitar un loop infinito de reintentos.
    """
    try:
        message = json.loads(body)   # Convertimos el JSON del mensaje a diccionario
        task_id = message["task_id"]
        payload = message["payload"] # Datos del pedido enviados por la API

        logger.info(f"Procesando creación para task_id={task_id}")

        order_id = str(uuid.uuid4())  # Generamos el ID del pedido aquí en el Worker
        now = datetime.now(timezone.utc)

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            # Guardamos el payload como JSONB para poder hacer consultas flexibles después
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

        # Marcamos la tarea como completada para que el cliente lo sepa
        update_task_status(task_id, "completado")
        # Le decimos a RabbitMQ que el mensaje fue procesado correctamente
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error procesando mensaje de creación: {e}")
        # Rechazamos el mensaje sin reencolar para evitar loops infinitos
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def handle_delete(ch, method, properties, body):
    """Procesa un mensaje de la cola 'orders_delete'.

    Pasos:
    1. Deserializa el mensaje JSON
    2. Ejecuta DELETE en la tabla 'orders' de PostgreSQL
    3. Actualiza la tarea a 'completado'
    4. Confirma el mensaje a RabbitMQ
    """
    try:
        message = json.loads(body)
        task_id = message["task_id"]
        order_id = message["order_id"]  # ID del pedido a eliminar

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


# =============================================================================
# Lógica de consumo con reconexión automática
# =============================================================================

def consume_queue(queue: str, callback, rabbitmq_host: str) -> None:
    """Consume mensajes de una cola de RabbitMQ indefinidamente.

    Si la conexión se cae (ej: RabbitMQ se reinicia), espera 10 segundos
    y vuelve a intentar. Esto hace al Worker resiliente a fallos temporales.

    prefetch_count=1 significa que el Worker solo toma un mensaje a la vez,
    garantizando que los mensajes se distribuyan equitativamente si hubiera
    múltiples Workers corriendo.
    """
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
            channel.basic_qos(prefetch_count=1)  # Procesar de uno en uno
            channel.basic_consume(queue=queue, on_message_callback=callback)
            logger.info(f"Consumiendo cola: {queue}")
            channel.start_consuming()  # Bloquea el hilo esperando mensajes
        except Exception as e:
            logger.error(f"Worker para cola {queue} falló: {e}. Reconectando en 10s...")
            time.sleep(10)


# =============================================================================
# Punto de entrada — arranca los dos hilos consumidores
# =============================================================================

def main():
    """Arranca el Worker con dos hilos paralelos:
    - Hilo 1: consume la cola 'orders_create'
    - Hilo 2: consume la cola 'orders_delete'

    Ambos hilos son 'daemon=True' lo que significa que se cierran automáticamente
    cuando el proceso principal termina.
    """
    logger.info("Iniciando worker...")
    rabbitmq_host = get_rabbitmq_host()
    logger.info(f"Host RabbitMQ: {rabbitmq_host}")

    # Hilo para procesar creaciones de pedidos
    create_thread = threading.Thread(
        target=consume_queue,
        args=("orders_create", handle_create, rabbitmq_host),
        daemon=True,
    )
    # Hilo para procesar eliminaciones de pedidos
    delete_thread = threading.Thread(
        target=consume_queue,
        args=("orders_delete", handle_delete, rabbitmq_host),
        daemon=True,
    )

    create_thread.start()
    delete_thread.start()

    logger.info("Hilos del worker iniciados. Esperando mensajes...")
    # join() hace que el proceso principal espere a que los hilos terminen (nunca terminan)
    create_thread.join()
    delete_thread.join()


if __name__ == "__main__":
    main()
