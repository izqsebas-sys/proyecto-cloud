# =============================================================================
# security_groups.tf — Reglas de Firewall para cada servicio
# =============================================================================
# Los Security Groups son el firewall de AWS. Cada instancia EC2 tiene su propio
# grupo con reglas específicas según lo que necesita exponer.
#
# Principio aplicado: mínimo privilegio — cada instancia solo abre los puertos
# que realmente necesita. El Worker, por ejemplo, no abre ningún puerto de entrada.
# =============================================================================

# -----------------------------------------------------------------------------
# PostgreSQL — Solo acepta conexiones en el puerto de base de datos (5432)
# -----------------------------------------------------------------------------
resource "aws_security_group" "sg_postgres" {
  name        = "proyecto-sg-postgres"
  description = "PostgreSQL security group"
  vpc_id      = var.vpc_id

  # Puerto SSH — para administración y depuración manual de la instancia
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Puerto 5432 — puerto estándar de PostgreSQL para conexiones de la API y el Worker
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Salida sin restricciones — necesario para que PostgreSQL pueda responder
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "proyecto-sg-postgres" }
}

# -----------------------------------------------------------------------------
# RabbitMQ — Expone el puerto AMQP y la interfaz web de administración
# -----------------------------------------------------------------------------
resource "aws_security_group" "sg_rabbitmq" {
  name        = "proyecto-sg-rabbitmq"
  description = "RabbitMQ security group"
  vpc_id      = var.vpc_id

  # Puerto SSH — para administración
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Puerto 5672 — protocolo AMQP, por donde la API publica y el Worker consume mensajes
  ingress {
    from_port   = 5672
    to_port     = 5672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Puerto 15672 — interfaz web de administración de RabbitMQ (http://ip:15672)
  # Permite ver las colas, mensajes pendientes y estadísticas en tiempo real
  ingress {
    from_port   = 15672
    to_port     = 15672
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "proyecto-sg-rabbitmq" }
}

# -----------------------------------------------------------------------------
# API — Solo expone el puerto de la aplicación FastAPI
# -----------------------------------------------------------------------------
resource "aws_security_group" "sg_api" {
  name        = "proyecto-sg-api"
  description = "API security group"
  vpc_id      = var.vpc_id

  # Puerto SSH — para administración
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Puerto 8000 — donde corre uvicorn (servidor de FastAPI) dentro del contenedor Docker
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "proyecto-sg-api" }
}

# -----------------------------------------------------------------------------
# HAProxy — El único punto de entrada público, acepta tráfico HTTP en puerto 80
# -----------------------------------------------------------------------------
resource "aws_security_group" "sg_haproxy" {
  name        = "proyecto-sg-haproxy"
  description = "HAProxy load balancer security group"
  vpc_id      = var.vpc_id

  # Puerto SSH — para administración
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Puerto 80 — tráfico HTTP público. HAProxy lo recibe y lo reenvía a las APIs en el 8000
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "proyecto-sg-haproxy" }
}

# -----------------------------------------------------------------------------
# Worker — No necesita recibir conexiones, solo hace conexiones salientes
# -----------------------------------------------------------------------------
# El Worker se conecta a RabbitMQ y PostgreSQL pero nadie se conecta a él.
# Solo tiene SSH abierto para diagnósticos manuales.
resource "aws_security_group" "sg_worker" {
  name        = "proyecto-sg-worker"
  description = "Worker security group"
  vpc_id      = var.vpc_id

  # Puerto SSH — único puerto de entrada, solo para administración
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Salida sin restricciones — necesita conectarse a RabbitMQ (5672) y PostgreSQL (5432)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "proyecto-sg-worker" }
}
