output "service_host" {
  value       = helm_release.kafka_ui.values["service.host"]
  description = "Kafka UI service host"
}

output "service_port" {
  value       = helm_release.kafka_ui.values["service.port"]
  description = "Kafka UI service port"
}