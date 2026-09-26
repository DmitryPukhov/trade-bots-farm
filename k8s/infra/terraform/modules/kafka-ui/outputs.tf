output "service_host" {
  value       = var.enabled ? "kafka-ui.${var.namespace}.svc.cluster.local" : ""
  description = "Kafka UI service host"
}

output "service_port" {
  value       = var.enabled ? 80 : 0
  description = "Kafka UI service port"
}