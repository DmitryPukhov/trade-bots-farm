output "bootstrap_servers" {
  value       = "my-cluster-kafka-bootstrap.${var.namespace}.svc.cluster.local:9092"
  description = "Kafka bootstrap servers"
}