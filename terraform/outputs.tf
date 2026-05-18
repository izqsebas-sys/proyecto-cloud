output "haproxy_public_ip" {
  description = "Public IP of the HAProxy load balancer (API entry point)"
  value       = aws_instance.haproxy.public_ip
}

output "api_1_public_ip" {
  description = "Public IP of API instance 1"
  value       = aws_instance.api_1.public_ip
}

output "api_2_public_ip" {
  description = "Public IP of API instance 2"
  value       = aws_instance.api_2.public_ip
}

output "rabbitmq_public_ip" {
  description = "Public IP of RabbitMQ (management UI at :15672)"
  value       = aws_instance.rabbitmq.public_ip
}

output "postgres_public_ip" {
  description = "Public IP of PostgreSQL"
  value       = aws_instance.postgres.public_ip
}

output "worker_public_ip" {
  description = "Public IP of the Worker"
  value       = aws_instance.worker.public_ip
}

output "api_swagger_url" {
  description = "Swagger UI URL"
  value       = "http://${aws_instance.haproxy.public_ip}/docs"
}
