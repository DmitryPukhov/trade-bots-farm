output "connect_url" {
  value       = var.enabled ? "kafka-connect-s3-connect-api.${var.namespace}.svc.cluster.local:8083" : ""
  description = "Kafka Connect API URL"
}

output "connect_cluster" {
  value       = var.enabled ? "kafka-connect-s3" : ""
  description = "Kafka Connect cluster name (used in KafkaConnector labels)"
}