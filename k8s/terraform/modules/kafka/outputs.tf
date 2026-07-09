output "bootstrap_servers" {
  value       = "trade-bots-farm-kafka-bootstrap.${var.namespace}.svc.cluster.local:9092"
  description = "Kafka bootstrap servers (internal, plaintext)"
}

output "external_bootstrap_servers" {
  value       = "${var.ingress_host}:31094"
  description = "Kafka bootstrap servers for external clients via nodeport 31094. Plaintext, no TLS. Point DNS for the hostname at any cluster node IP."
}

output "kafka_connect_url" {
  value       = "trade-bots-farm-kafka-connect-api.${var.namespace}.svc.cluster.local:8083"
  description = "Kafka Connect API URL"
}