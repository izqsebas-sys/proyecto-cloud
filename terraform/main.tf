# =============================================================================
# main.tf — Instancias EC2 y Parámetros SSM
# =============================================================================
# Este archivo define las 6 instancias EC2 del proyecto y los parámetros SSM
# que permiten que los servicios se comuniquen entre sí sin hardcodear IPs.
#
# Todas las instancias usan el mismo AMI (Amazon Linux 2023) y tipo t3.micro
# porque estamos en AWS Learner Lab que tiene restricciones de créditos.
# El user_data de cada instancia ejecuta el script de instalación automáticamente
# la primera vez que la máquina arranca.
# =============================================================================

# Leemos el rol IAM del Learner Lab que ya existe en la cuenta.
# Este rol tiene los permisos necesarios para acceder a SSM Parameter Store.
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# -----------------------------------------------------------------------------
# PostgreSQL — Base de datos relacional del sistema
# -----------------------------------------------------------------------------
# Una sola instancia EC2 corre el servidor PostgreSQL.
# Los datos de pedidos y tareas se guardan aquí permanentemente.
resource "aws_instance" "postgres" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.sg_postgres.id]
  key_name               = var.key_name
  iam_instance_profile   = "LabInstanceProfile"  # Necesario para acceder a SSM

  # install_postgres.sh crea la BD, las tablas y el usuario appuser automáticamente
  user_data = templatefile("${path.module}/install_postgres.sh", {
    db_password = var.db_password
  })

  tags = { Name = "proyecto-postgres" }
}

# -----------------------------------------------------------------------------
# RabbitMQ — Broker de mensajes para el flujo asíncrono
# -----------------------------------------------------------------------------
# Una sola instancia EC2 corre el servidor RabbitMQ con Docker.
# La API publica mensajes aquí y el Worker los consume.
resource "aws_instance" "rabbitmq" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.sg_rabbitmq.id]
  key_name               = var.key_name
  iam_instance_profile   = "LabInstanceProfile"

  user_data = templatefile("${path.module}/install_rabbitmq.sh", {})

  tags = { Name = "proyecto-rabbitmq" }
}

# -----------------------------------------------------------------------------
# API Instancia 1 — Servidor FastAPI detrás del balanceador
# -----------------------------------------------------------------------------
# La API corre en Docker para facilitar el despliegue y aislar dependencias.
# HAProxy distribuye el tráfico entre api_1 y api_2 con round-robin.
resource "aws_instance" "api_1" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.sg_api.id]
  key_name               = var.key_name
  iam_instance_profile   = "LabInstanceProfile"

  # El script clona el repositorio de GitHub y construye la imagen Docker
  user_data = templatefile("${path.module}/install_api.sh", {
    repo_url    = var.repo_url
    db_password = var.db_password
  })

  tags = { Name = "proyecto-api-1" }
}

# -----------------------------------------------------------------------------
# API Instancia 2 — Segunda instancia para alta disponibilidad
# -----------------------------------------------------------------------------
# Instancia idéntica a api_1. Con dos instancias, si una falla el sistema sigue
# funcionando. Además permite distribuir la carga en momentos de alto tráfico.
resource "aws_instance" "api_2" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.sg_api.id]
  key_name               = var.key_name
  iam_instance_profile   = "LabInstanceProfile"

  user_data = templatefile("${path.module}/install_api.sh", {
    repo_url    = var.repo_url
    db_password = var.db_password
  })

  tags = { Name = "proyecto-api-2" }
}

# -----------------------------------------------------------------------------
# HAProxy — Balanceador de carga
# -----------------------------------------------------------------------------
# HAProxy es el único componente con IP pública accesible desde internet.
# Recibe todas las peticiones en el puerto 80 y las distribuye entre api_1 y api_2.
# Las IPs privadas de las APIs se inyectan directamente en el script de configuración.
resource "aws_instance" "haproxy" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.sg_haproxy.id]
  key_name               = var.key_name
  iam_instance_profile   = "LabInstanceProfile"

  # Pasamos las IPs privadas de las APIs al script de configuración de HAProxy
  user_data = templatefile("${path.module}/install_haproxy.sh", {
    api_ip_1 = aws_instance.api_1.private_ip
    api_ip_2 = aws_instance.api_2.private_ip
  })

  tags = { Name = "proyecto-haproxy" }
}

# -----------------------------------------------------------------------------
# Worker — Consumidor de colas RabbitMQ
# -----------------------------------------------------------------------------
# El Worker corre en su propia instancia para no competir por recursos con la API.
# No necesita IP pública porque solo hace conexiones salientes (a RabbitMQ y PostgreSQL).
resource "aws_instance" "worker" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.sg_worker.id]
  key_name               = var.key_name
  iam_instance_profile   = "LabInstanceProfile"

  user_data = templatefile("${path.module}/install_worker.sh", {
    repo_url    = var.repo_url
    db_password = var.db_password
  })

  tags = { Name = "proyecto-worker" }
}

# =============================================================================
# SSM Parameter Store — Directorio centralizado de configuración
# =============================================================================
# En lugar de hardcodear IPs en los scripts (que cambian con cada sesión del
# Learner Lab), guardamos las IPs en SSM y la API/Worker las leen al arrancar.
# Esto es el equivalente cloud a un archivo .env compartido.

# IP privada de RabbitMQ — la API y el Worker la necesitan para conectarse
resource "aws_ssm_parameter" "rabbitmq_host" {
  name  = "/proyecto/rabbitmq_host"
  type  = "String"
  value = aws_instance.rabbitmq.private_ip
}

# IP privada de PostgreSQL — la API y el Worker la necesitan para la base de datos
resource "aws_ssm_parameter" "postgres_host" {
  name  = "/proyecto/postgres_host"
  type  = "String"
  value = aws_instance.postgres.private_ip
}

# IP pública de HAProxy — el Producer la necesita para enviar pedidos
resource "aws_ssm_parameter" "haproxy_ip" {
  name  = "/proyecto/haproxy_ip"
  type  = "String"
  value = aws_instance.haproxy.public_ip
}
