# Async Orders API — Cloud Project

Asynchronous order processing system deployed on AWS EC2 with FastAPI, RabbitMQ, PostgreSQL, and HAProxy load balancer. Infrastructure is managed with Terraform (OpenTofu compatible).

## Architecture

```
Producer → HAProxy (port 80) → API-1 (port 8000)  → PostgreSQL
                             ↘ API-2 (port 8000)  → RabbitMQ → Worker → PostgreSQL
```

| Component | EC2 | Purpose |
|-----------|-----|---------|
| PostgreSQL | 1 | Persistent storage for Tasks and Orders |
| RabbitMQ | 1 | Message broker for async processing |
| API | 2 | FastAPI application servers |
| HAProxy | 1 | Load balancer (round-robin across 2 APIs) |
| Worker | 1 | Consumes RabbitMQ queues, processes orders |

All service IPs are stored and read from **AWS SSM Parameter Store**.

## API Endpoints

| Method | Path | Type | Description |
|--------|------|------|-------------|
| GET | `/health` | sync | Health check |
| POST | `/orders` | async | Create order → returns 202 + task_id |
| GET | `/orders` | sync | List all orders |
| PUT | `/orders/{order_id}` | sync | Update order payload |
| DELETE | `/orders/{order_id}` | async | Delete order → returns 202 + task_id |
| GET | `/tasks/{task_id}` | sync | Check async task status |

Swagger UI available at: `http://<haproxy_ip>/docs`

## Prerequisites

- Docker (dev container from `0_dev_environment/`)
- AWS Learner Lab credentials configured (`aws configure`)
- Terraform >= 1.11.3
- GitHub repository with this code

## Deployment

### 1. Start the dev container

```bash
cd ../0_dev_environment
docker build -t iot_dev_environment_image .
docker run -it --name dev -v $(pwd)/..:/app iot_dev_environment_image bash
```

### 2. Configure AWS credentials

```bash
aws configure
# Enter: Access Key ID, Secret Access Key, region=us-east-1, output=json
```

### 3. Set your GitHub repo URL

Edit `terraform/variables.tf` and update `repo_url` with your actual GitHub repository URL.

### 4. Deploy infrastructure

```bash
cd proyecto/terraform
terraform init
terraform apply -auto-approve
```

Note the outputs — especially `haproxy_public_ip` and `api_swagger_url`.

### 5. Destroy infrastructure

```bash
terraform destroy -auto-approve
```

## Local Development

### Run API locally

```bash
cd api
pip install -r requirements.txt
export POSTGRES_HOST=localhost
export RABBITMQ_HOST=localhost
uvicorn main:app --reload --port 8000
```

### Run tests

```bash
cd api
pip install -r requirements.txt pytest httpx
pytest tests/ -v
```

### Static analysis (ruff)

```bash
pip install ruff
ruff check api/ worker/ producer/
```

## Usage Examples

### Create an order (async)

```bash
curl -X POST http://<haproxy_ip>/orders \
  -H "Content-Type: application/json" \
  -d '{"description": "New order", "quantity": 3, "product": "Widget A"}'
# Returns: {"task_id": "uuid", "status": "pending"}
```

### Check task status

```bash
curl http://<haproxy_ip>/tasks/<task_id>
# Returns: {"task_id": "...", "status": "completed", "created_at": "..."}
```

### List all orders

```bash
curl http://<haproxy_ip>/orders
```

### Update an order (sync)

```bash
curl -X PUT http://<haproxy_ip>/orders/<order_id> \
  -H "Content-Type: application/json" \
  -d '{"quantity": 10}'
```

### Delete an order (async)

```bash
curl -X DELETE http://<haproxy_ip>/orders/<order_id>
# Returns: {"task_id": "uuid", "status": "pending"}
```

### Run the synthetic producer

```bash
cd producer
pip install -r requirements.txt
export API_URL=<haproxy_ip>
python producer.py
```

## SSM Parameters

Terraform automatically stores these in SSM Parameter Store:

| Parameter | Value |
|-----------|-------|
| `/proyecto/postgres_host` | Private IP of PostgreSQL EC2 |
| `/proyecto/rabbitmq_host` | Private IP of RabbitMQ EC2 |
| `/proyecto/haproxy_ip` | Public IP of HAProxy EC2 |

The API and Worker read these parameters automatically via `boto3` at runtime.

## Async Flow

1. `POST /orders` → creates Task (status=`pending`) in PostgreSQL → publishes to `orders_create` queue → returns **202** + `task_id`
2. Worker consumes `orders_create` → creates Order in PostgreSQL → updates Task status to `completed`
3. Client polls `GET /tasks/{task_id}` until status = `completed`

## Project Structure

```
proyecto/
├── README.md
├── pyproject.toml          # Ruff configuration
├── api/
│   ├── main.py             # FastAPI application
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       ├── conftest.py
│       └── test_main.py    # Unit tests (pytest)
├── worker/
│   ├── worker.py           # RabbitMQ consumer
│   ├── requirements.txt
│   └── Dockerfile
├── producer/
│   ├── producer.py         # Synthetic event generator
│   └── requirements.txt
└── terraform/
    ├── main.tf             # EC2 instances + SSM parameters
    ├── providers.tf
    ├── variables.tf
    ├── outputs.tf
    ├── security_groups.tf
    ├── Makefile
    ├── install_postgres.sh
    ├── install_rabbitmq.sh
    ├── install_api.sh
    ├── install_haproxy.sh
    └── install_worker.sh
```
