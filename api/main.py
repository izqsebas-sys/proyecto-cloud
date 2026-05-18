# =============================================================================
# API Principal — Sistema de Pedidos Asíncronos
# =============================================================================
# Este archivo contiene toda la lógica de la API REST construida con FastAPI.
# La API recibe pedidos del cliente, los guarda en PostgreSQL y los envía a
# RabbitMQ para que el Worker los procese en segundo plano.
# =============================================================================

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import boto3        # SDK oficial de AWS para leer parámetros de SSM
import pika         # Librería para conectarse y publicar mensajes en RabbitMQ
import psycopg2     # Conector de Python para bases de datos PostgreSQL
from fastapi import FastAPI, HTTPException  # Framework web y manejo de errores HTTP
from pydantic import BaseModel              # Validación automática de datos de entrada

# Configuramos el sistema de logs para ver lo que pasa mientras la API corre
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Creamos la aplicación FastAPI con título y descripción que aparecen en el Swagger
app = FastAPI(
    title="API de Pedidos Asíncronos",
    description="API de procesamiento asíncrono de pedidos con RabbitMQ y PostgreSQL",
    version="1.0.0",
)

# Caché en memoria para no consultar SSM repetidamente en cada petición
_config_cache: dict = {}


def _validar_uuid(valor: str, mensaje_404: str = "Recurso no encontrado") -> None:
    """Verifica que el valor sea un UUID válido antes de consultarlo en la base de datos.
    Si el formato es inválido retorna 404 directamente, evitando un error 500 de PostgreSQL."""
    try:
        uuid.UUID(valor)
    except ValueError:
        raise HTTPException(status_code=404, detail=mensaje_404)


# =============================================================================
# Funciones de configuración — Lectura de IPs desde AWS SSM Parameter Store
# =============================================================================
# En AWS Learner Lab no podemos hardcodear IPs porque cambian con cada sesión.
# SSM Parameter Store es el servicio de AWS para guardar configuración centralizada.

def get_ssm_parameter(name: str, retries: int = 10, delay: int = 15) -> str:
    """Obtiene un parámetro de SSM con reintentos, porque las instancias EC2
    pueden tardar unos segundos en registrar sus IPs al arrancar."""
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
    """Primero busca la configuración en variables de entorno (útil para desarrollo local),
    si no la encuentra la pide a SSM (modo producción en AWS)."""
    if key not in _config_cache:
        value = os.environ.get(env_var)
        if not value:
            value = get_ssm_parameter(ssm_name)
        _config_cache[key] = value
    return _config_cache[key]


def get_postgres_host() -> str:
    """Retorna la IP privada del servidor PostgreSQL."""
    return get_config("postgres_host", "POSTGRES_HOST", "/proyecto/postgres_host")


def get_rabbitmq_host() -> str:
    """Retorna la IP privada del servidor RabbitMQ."""
    return get_config("rabbitmq_host", "RABBITMQ_HOST", "/proyecto/rabbitmq_host")


# =============================================================================
# Funciones de conexión a servicios externos
# =============================================================================

def get_db_connection():
    """Abre una nueva conexión a PostgreSQL usando las credenciales configuradas."""
    return psycopg2.connect(
        host=get_postgres_host(),
        database=os.environ.get("DB_NAME", "ordersdb"),
        user=os.environ.get("DB_USER", "appuser"),
        password=os.environ.get("DB_PASSWORD", "apppassword"),
        port=int(os.environ.get("DB_PORT", "5432")),
    )


def get_rabbitmq_channel():
    """Abre una conexión a RabbitMQ y declara las dos colas que usa el sistema.
    'durable=True' garantiza que los mensajes sobrevivan si RabbitMQ se reinicia."""
    credentials = pika.PlainCredentials(
        os.environ.get("RABBITMQ_USER", "user"),
        os.environ.get("RABBITMQ_PASSWORD", "password"),
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=get_rabbitmq_host(), credentials=credentials)
    )
    channel = connection.channel()
    # Declaramos las colas como durables para no perder mensajes ante reinicios
    channel.queue_declare(queue="orders_create", durable=True)
    channel.queue_declare(queue="orders_delete", durable=True)
    return connection, channel


def publish_message(queue: str, message: dict) -> None:
    """Publica un mensaje en la cola indicada de RabbitMQ.
    delivery_mode=2 hace el mensaje persistente en disco."""
    connection, channel = get_rabbitmq_channel()
    try:
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        connection.close()  # Siempre cerramos la conexión aunque haya errores


# =============================================================================
# Modelos de datos — Definen la estructura de los JSON que recibe la API
# =============================================================================

class OrderCreate(BaseModel):
    """Datos requeridos para crear un nuevo pedido."""
    description: str   # Descripción del pedido
    quantity: int      # Cantidad de unidades
    product: str       # Nombre del producto


class OrderUpdate(BaseModel):
    """Datos opcionales para actualizar un pedido existente.
    Todos los campos son opcionales — solo se actualiza lo que se envíe."""
    description: Optional[str] = None
    quantity: Optional[int] = None
    product: Optional[str] = None


# =============================================================================
# Endpoints de la API
# =============================================================================

@app.get("/health")
def health_check():
    """Endpoint simple para verificar que la API está viva.
    HAProxy y los monitores de salud llaman a este endpoint periódicamente."""
    return {"estado": "saludable"}


@app.post("/orders", status_code=202)
def create_order(order: OrderCreate):
    """Crea un nuevo pedido de forma ASÍNCRONA.

    Flujo:
    1. Genera un task_id único (UUID)
    2. Guarda la tarea como 'pendiente' en PostgreSQL
    3. Publica el pedido en la cola 'orders_create' de RabbitMQ
    4. Retorna 202 (Aceptado) con el task_id para que el cliente haga seguimiento

    El Worker procesará el mensaje en segundo plano y actualizará el estado a 'completado'.
    """
    task_id = str(uuid.uuid4())  # Identificador único para rastrear esta operación
    now = datetime.now(timezone.utc)

    # Paso 1: Guardar la tarea en la base de datos con estado 'pendiente'
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

    # Paso 2: Publicar el pedido en RabbitMQ para procesamiento asíncrono
    try:
        publish_message("orders_create", {"task_id": task_id, "payload": order.model_dump()})
    except Exception as e:
        logger.error(f"Error de RabbitMQ: {e}")
        raise HTTPException(status_code=500, detail="Error al encolar el pedido")

    logger.info(f"Pedido encolado con task_id={task_id}")
    return {"task_id": task_id, "estado": "pendiente"}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    """Consulta el estado de una tarea asíncrona.

    El cliente llama a este endpoint repetidamente después de crear/eliminar un pedido
    para saber si el Worker ya terminó de procesar la operación.
    Estados posibles: 'pendiente' → 'completado'
    """
    # Validamos el formato UUID antes de consultar la BD para evitar error 500
    _validar_uuid(task_id, "Tarea no encontrada")
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
    """Retorna la lista completa de pedidos almacenados en PostgreSQL,
    ordenados del más reciente al más antiguo."""
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
            "datos": r[2],          # JSONB de PostgreSQL, se retorna como diccionario Python
            "creado_en": str(r[3]),
        }
        for r in rows
    ]


@app.put("/orders/{order_id}")
def update_order(order_id: str, order: OrderUpdate):
    """Actualiza los datos de un pedido existente de forma SÍNCRONA.

    Usa el operador '||' de JSONB en PostgreSQL para fusionar los nuevos valores
    con los existentes. Solo se actualizan los campos que se envíen en el cuerpo.
    """
    _validar_uuid(order_id, "Pedido no encontrado")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Primero verificamos que el pedido exista antes de intentar actualizar
        cur.execute("SELECT order_id FROM orders WHERE order_id = %s", (order_id,))
        if not cur.fetchone():
            cur.close()
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        # Construimos el diccionario solo con los campos que el cliente envió
        updates = {k: v for k, v in order.model_dump().items() if v is not None}
        if updates:
            # '||' en PostgreSQL fusiona dos objetos JSONB (como Object.assign en JS)
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
    """Elimina un pedido de forma ASÍNCRONA.

    Al igual que la creación, la eliminación no se hace de inmediato.
    Se genera una tarea, se encola en RabbitMQ y el Worker ejecuta el DELETE.
    Esto permite que el cliente sepa exactamente cuándo se completó la eliminación.
    """
    _validar_uuid(order_id, "Pedido no encontrado")

    # Verificamos que el pedido exista antes de encolar la eliminación
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

    # Creamos la tarea de eliminación en la base de datos
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

    # Enviamos la orden de eliminación al Worker a través de RabbitMQ
    try:
        publish_message("orders_delete", {"task_id": task_id, "order_id": order_id})
    except Exception as e:
        logger.error(f"Error de RabbitMQ: {e}")
        raise HTTPException(status_code=500, detail="Error al encolar la eliminación")

    logger.info(f"Eliminación encolada para pedido={order_id}, task_id={task_id}")
    return {"task_id": task_id, "estado": "pendiente"}
