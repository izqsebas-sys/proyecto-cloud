# =============================================================================
# variables.tf — Parámetros configurables de la infraestructura
# =============================================================================
# Centralizar los valores en variables evita buscar y cambiar datos en múltiples
# archivos. Para una nueva sesión del Learner Lab solo hay que actualizar
# vpc_id y subnet_id aquí.
# =============================================================================

# ID de la red virtual donde viven todas las instancias.
# Cambiar por el VPC de la sesión actual del Learner Lab.
variable "vpc_id" {
  description = "VPC ID para el proyecto"
  type        = string
  default     = "vpc-055b57b4906f95f03"
}

# ID de la subred donde se crearán todas las EC2.
# Usamos us-east-1a para que todas estén en la misma zona de disponibilidad
# y la latencia entre ellas sea mínima.
variable "subnet_id" {
  description = "ID de subred para las instancias EC2"
  type        = string
  default     = "subnet-09ae42c851723e9d3"
}

# AMI de Amazon Linux 2023 en us-east-1.
# Amazon Linux 2023 viene con soporte nativo para Docker y los paquetes
# que necesitan los scripts de instalación (dnf, systemd).
variable "ami_id" {
  description = "ID de la AMI Amazon Linux 2023"
  type        = string
  default     = "ami-02dfbd4ff395f2a1b"
}

# Tipo de instancia. t3.micro tiene 2 vCPU y 1 GB de RAM.
# Es suficiente para este proyecto de laboratorio y entra en el free tier.
variable "instance_type" {
  description = "Tipo de instancia EC2"
  type        = string
  default     = "t3.micro"
}

# Nombre del par de llaves SSH para conectarse a las instancias.
# 'vockey' es el key pair estándar que provee AWS Academy en el Learner Lab.
variable "key_name" {
  description = "Nombre del key pair de EC2"
  type        = string
  default     = "vockey"
}

# URL del repositorio GitHub desde donde las instancias clonan el código.
# Los scripts de instalación hacen 'git clone' de esta URL al arrancar.
variable "repo_url" {
  description = "URL del repositorio GitHub para clonar el proyecto"
  type        = string
  default     = "https://github.com/izqsebas-sys/proyecto-cloud.git"
}

# Contraseña del usuario de base de datos. Marcada como 'sensitive' para
# que Terraform no la muestre en los logs ni en el plan.
variable "db_password" {
  description = "Contraseña del usuario PostgreSQL"
  type        = string
  default     = "apppassword"
  sensitive   = true
}
