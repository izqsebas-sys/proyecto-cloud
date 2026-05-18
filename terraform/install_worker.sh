#!/bin/bash
set -e

REPO_URL="${repo_url}"
DB_PASSWORD="${db_password}"

sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

cd /home/ec2-user
git clone "$REPO_URL" app
cd app/worker

sudo docker build -t orders-worker .

sudo docker run -d \
  --name orders-worker \
  --restart=always \
  -e DB_NAME=ordersdb \
  -e DB_USER=appuser \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e DB_PORT=5432 \
  -e RABBITMQ_USER=user \
  -e RABBITMQ_PASSWORD=password \
  orders-worker

echo "Worker setup complete"
