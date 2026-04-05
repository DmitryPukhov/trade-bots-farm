output "service_host" {
  value       = helm_release.mlflow.values["service.host"]
  description = "MLflow service host"
}

output "service_port" {
  value       = helm_release.mlflow.values["service.port"]
  description = "MLflow service port"
}