import logging
import os
import random
import time

import boto3
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PRODUCTS = ["Widget A", "Widget B", "Gadget X", "Tool Z", "Device Pro"]
NUM_EVENTS = 10
DELAY_SECONDS = 2


def get_ssm_parameter(name: str) -> str:
    ssm = boto3.client("ssm", region_name="us-east-1")
    response = ssm.get_parameter(Name=name)
    return response["Parameter"]["Value"]


def get_api_url() -> str:
    host = os.environ.get("API_URL")
    if not host:
        host = get_ssm_parameter("/proyecto/haproxy_ip")
    return f"http://{host}"


def send_order(api_url: str, payload: dict) -> dict:
    response = requests.post(f"{api_url}/orders", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def check_task(api_url: str, task_id: str) -> dict:
    response = requests.get(f"{api_url}/tasks/{task_id}", timeout=10)
    response.raise_for_status()
    return response.json()


def main():
    api_url = get_api_url()
    logger.info(f"Sending synthetic events to: {api_url}")

    task_ids = []

    for i in range(1, NUM_EVENTS + 1):
        payload = {
            "description": f"Synthetic order {i}",
            "quantity": random.randint(1, 10),
            "product": random.choice(PRODUCTS),
        }
        try:
            result = send_order(api_url, payload)
            task_id = result.get("task_id")
            task_ids.append(task_id)
            logger.info(
                f"[{i}/{NUM_EVENTS}] Order sent → task_id={task_id}, product={payload['product']}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"[{i}/{NUM_EVENTS}] Failed to send order: {e}")

        if i < NUM_EVENTS:
            time.sleep(DELAY_SECONDS)

    logger.info("All events sent. Checking task statuses...")
    time.sleep(3)

    for task_id in task_ids:
        try:
            task = check_task(api_url, task_id)
            logger.info(f"Task {task_id} → status={task.get('status')}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check task {task_id}: {e}")


if __name__ == "__main__":
    main()
