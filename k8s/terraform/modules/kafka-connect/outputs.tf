output "build_status" {
  value       = var.enabled ? resource.kubernetes_pod.kafka_connect_build[0].id : ""
  description = "Kafka Connect build status"
}