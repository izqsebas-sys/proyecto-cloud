# =============================================================================
# Producer — Generador Sintético de Pedidos
# =============================================================================
# Este script simula clientes reales enviando pedidos a la API.
# Se usa para probar el sistema con carga real sin necesidad de una interfaz
# gráfica o clientes externos.
#
# Envía NUM_EVENTS pedidos con datos aleatorios, espera un poco y luego
# verifica que todos hayan sido procesados correctamente por el Worker.
# =============================================================================

import logging
import os
import random
import time

import boto3      # Para obtener la IP del balanceador desde SSM
import requests   # Librería HTTP para hacer llamadas a la API REST

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Lista de productos de prueba para generar pedidos variados
PRODUCTS = ["Widget A", "Widget B", "Gadget X", "Tool Z", "Device Pro"]
NUM_EVENTS = 10       # Cantidad de pedidos a enviar
DELAY_SECONDS = 2     # Segundos de espera entre pedido y pedido


def get_ssm_parameter(name: str) -> str:
    """Lee un parámetro de SSM. El Producer no necesita reintentos porque
    se ejecuta manualmente después de que la infraestructura ya está lista."""
    ssm = boto3.client("ssm", region_name="us-east-1")
    response = ssm.get_parameter(Name=name)
    return response["Parameter"]["Value"]


def get_api_url() -> str:
    """Obtiene la URL base de la API. Primero busca en la variable de entorno API_URL
    (para pruebas locales), si no la encuentra consulta SSM para obtener la IP del HAProxy."""
    host = os.environ.get("API_URL")
    if not host:
        host = get_ssm_parameter("/proyecto/haproxy_ip")
    return f"http://{host}"


def send_order(api_url: str, payload: dict) -> dict:
    """Envía un pedido a POST /orders y retorna la respuesta con el task_id."""
    response = requests.post(f"{api_url}/orders", json=payload, timeout=10)
    response.raise_for_status()  # Lanza excepción si el código HTTP es 4xx o 5xx
    return response.json()


def check_task(api_url: str, task_id: str) -> dict:
    """Consulta GET /tasks/{task_id} para ver si el Worker ya procesó el pedido."""
    response = requests.get(f"{api_url}/tasks/{task_id}", timeout=10)
    response.raise_for_status()
    return response.json()


def main():
    """Flujo principal del Producer:
    1. Obtiene la URL de la API
    2. Envía NUM_EVENTS pedidos con datos aleatorios, guardando cada task_id
    3. Espera 3 segundos para dar tiempo al Worker de procesar
    4. Verifica el estado final de cada tarea
    """
    api_url = get_api_url()
    logger.info(f"Enviando eventos sintéticos a: {api_url}")

    task_ids = []  # Lista para guardar los task_ids y verificarlos al final

    # Fase 1: Enviar pedidos
    for i in range(1, NUM_EVENTS + 1):
        payload = {
            "description": f"Pedido sintético {i}",
            "quantity": random.randint(1, 10),       # Cantidad aleatoria entre 1 y 10
            "product": random.choice(PRODUCTS),       # Producto aleatorio de la lista
        }
        try:
            result = send_order(api_url, payload)
            task_id = result.get("task_id")
            task_ids.append(task_id)
            logger.info(
                f"[{i}/{NUM_EVENTS}] Pedido enviado → task_id={task_id}, producto={payload['product']}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"[{i}/{NUM_EVENTS}] Error al enviar pedido: {e}")

        if i < NUM_EVENTS:
            time.sleep(DELAY_SECONDS)  # Pequeña pausa para no saturar la API

    # Fase 2: Verificar que todos los pedidos fueron procesados
    logger.info("Todos los eventos enviados. Verificando estados de tareas...")
    time.sleep(3)  # Esperamos a que el Worker tenga tiempo de procesar todo

    for task_id in task_ids:
        try:
            task = check_task(api_url, task_id)
            logger.info(f"Tarea {task_id} → estado={task.get('estado')}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al verificar tarea {task_id}: {e}")


if __name__ == "__main__":
    main()
