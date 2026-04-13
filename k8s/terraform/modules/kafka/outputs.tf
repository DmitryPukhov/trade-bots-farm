output "bootstrap_servers" {
  value       = "my-cluster-kafka-bootstrap.${var.namespace}.svc.cluster.local:9092"
  description = "Kafka bootstrap servers"
}

output "kafka_connect_url" {
  value       = "my-cluster-kafka-connect-api.${var.namespace}.svc.cluster.local:8083"
  description = "Kafka Connect API URL"
}