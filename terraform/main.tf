data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# --- PostgreSQL ---
resource "aws_instance" "postgres" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.sg_postgres.id]
  key_name               = var.key_name
  iam_instance_profile   = "LabInstanceProfile"

  user_data = templatefile("${path.module}/install_postgres.sh", {
    db_password = var.db_password
  })

  tags = { Name = "proyecto-postgres" }
}

# --- RabbitMQ ---
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

# --- API Instance 1 ---
resource "aws_instance" "api_1" {
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

  tags = { Name = "proyecto-api-1" }
}

# --- API Instance 2 ---
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

# --- HAProxy Load Balancer ---
resource "aws_instance" "haproxy" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.sg_haproxy.id]
  key_name               = var.key_name
  iam_instance_profile   = "LabInstanceProfile"

  user_data = templatefile("${path.module}/install_haproxy.sh", {
    api_ip_1 = aws_instance.api_1.private_ip
    api_ip_2 = aws_instance.api_2.private_ip
  })

  tags = { Name = "proyecto-haproxy" }
}

# --- Worker ---
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

# --- SSM Parameters ---
resource "aws_ssm_parameter" "rabbitmq_host" {
  name  = "/proyecto/rabbitmq_host"
  type  = "String"
  value = aws_instance.rabbitmq.private_ip
}

resource "aws_ssm_parameter" "postgres_host" {
  name  = "/proyecto/postgres_host"
  type  = "String"
  value = aws_instance.postgres.private_ip
}

resource "aws_ssm_parameter" "haproxy_ip" {
  name  = "/proyecto/haproxy_ip"
  type  = "String"
  value = aws_instance.haproxy.public_ip
}
