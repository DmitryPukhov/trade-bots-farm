output "service_host" {
  value       = var.enabled ? "minio.${var.namespace}.svc.cluster.local" : ""
  description = "MinIO service host"
}

output "service_port" {
  value       = var.enabled ? 80 : 0
  description = "MinIO service port"
}