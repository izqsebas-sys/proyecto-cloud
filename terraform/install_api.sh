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
cd app/api

sudo docker build -t orders-api .

sudo docker run -d \
  --name orders-api \
  --restart=always \
  -p 8000:8000 \
  -e DB_NAME=ordersdb \
  -e DB_USER=appuser \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e DB_PORT=5432 \
  -e RABBITMQ_USER=user \
  -e RABBITMQ_PASSWORD=password \
  orders-api

echo "API setup complete"
