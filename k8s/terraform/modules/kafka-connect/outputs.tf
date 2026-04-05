output "build_status" {
  value       = resource.kubernetes_pod.kafka_connect_build.id
  description = "Kafka Connect build status"
}