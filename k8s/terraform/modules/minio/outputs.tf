output "service_host" {
  value       = helm_release.minio.values["service.host"]
  description = "MinIO service host"
}

output "service_port" {
  value       = helm_release.minio.values["service.port"]
  description = "MinIO service port"
}