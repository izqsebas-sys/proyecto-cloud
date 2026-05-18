# =============================================================================
# providers.tf — Configuración del proveedor de nube
# =============================================================================
# Terraform necesita saber con qué nube va a trabajar.
# Aquí le decimos que use AWS en la región us-east-1 (Norte de Virginia),
# que es la región del AWS Learner Lab.
#
# La versión "~> 5.0" significa "cualquier versión 5.x" para evitar cambios
# incompatibles si HashiCorp lanza una versión 6.
# =============================================================================

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"  # Proveedor oficial de AWS mantenido por HashiCorp
      version = "~> 5.0"         # Versión mínima requerida
    }
  }
}

# Configuración del proveedor AWS.
# Las credenciales NO se escriben aquí — Terraform las lee automáticamente
# de las variables de entorno AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# y AWS_SESSION_TOKEN (que configuramos en la terminal del Learner Lab).
provider "aws" {
  region = "us-east-1"
}
