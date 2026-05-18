#!/bin/bash
set -e

DB_PASSWORD="${db_password}"

sudo dnf update -y
sudo dnf install -y postgresql15-server postgresql15

sudo postgresql-setup --initdb

sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /var/lib/pgsql/data/postgresql.conf

sudo bash -c "cat >> /var/lib/pgsql/data/pg_hba.conf << 'PGEOF'
host    all             all             0.0.0.0/0               md5
PGEOF"

sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo -u postgres psql << SQLEOF
CREATE USER appuser WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE ordersdb OWNER appuser;
GRANT ALL PRIVILEGES ON DATABASE ordersdb TO appuser;
SQLEOF

sudo -u postgres psql -d ordersdb << SQLEOF
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS tasks (
    task_id     UUID PRIMARY KEY,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    order_id    UUID PRIMARY KEY,
    task_id     UUID NOT NULL REFERENCES tasks(task_id),
    payload     JSONB NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO appuser;
SQLEOF

echo "PostgreSQL setup complete"
