output "bootstrap_servers" {
  value       = "trade-bots-farm-kafka-bootstrap.${var.namespace}.svc.cluster.local:9092"
  description = "Kafka bootstrap servers"
}

output "kafka_connect_url" {
  value       = "trade-bots-farm-kafka-connect-api.${var.namespace}.svc.cluster.local:8083"
  description = "Kafka Connect API URL"
}