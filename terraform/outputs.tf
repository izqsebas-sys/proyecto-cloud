# =============================================================================
# outputs.tf — Valores que Terraform muestra al terminar el 'apply'
# =============================================================================
# Los outputs son como el "resumen de resultado" de Terraform.
# Después de crear toda la infraestructura, estos valores se imprimen en pantalla
# para que sepamos las IPs sin tener que buscarlas en la consola de AWS.
# =============================================================================

# IP pública del balanceador — el único punto de entrada al sistema
output "haproxy_public_ip" {
  description = "IP pública del balanceador HAProxy (punto de entrada a la API)"
  value       = aws_instance.haproxy.public_ip
}

# IPs de las APIs — útiles para hacer pruebas directas sin pasar por el balanceador
output "api_1_public_ip" {
  description = "IP pública de la instancia API 1"
  value       = aws_instance.api_1.public_ip
}

output "api_2_public_ip" {
  description = "IP pública de la instancia API 2"
  value       = aws_instance.api_2.public_ip
}

# IP de RabbitMQ — para acceder a la interfaz web de administración en el puerto 15672
output "rabbitmq_public_ip" {
  description = "IP pública de RabbitMQ (interfaz web en :15672)"
  value       = aws_instance.rabbitmq.public_ip
}

# IP de PostgreSQL — para conexiones directas desde herramientas como DBeaver o psql
output "postgres_public_ip" {
  description = "IP pública de PostgreSQL"
  value       = aws_instance.postgres.public_ip
}

# IP del Worker — para ver sus logs y diagnosticar problemas de procesamiento
output "worker_public_ip" {
  description = "IP pública del Worker"
  value       = aws_instance.worker.public_ip
}

# URL directa al Swagger UI — para explorar y probar la API desde el navegador
output "api_swagger_url" {
  description = "URL del Swagger UI"
  value       = "http://${aws_instance.haproxy.public_ip}/docs"
}
