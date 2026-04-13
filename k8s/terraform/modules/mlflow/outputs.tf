output "service_host" {
  value       = var.enabled ? "mlflow.${var.namespace}.svc.cluster.local" : ""
  description = "MLflow service host"
}

output "service_port" {
  value       = var.enabled ? 80 : 0
  description = "MLflow service port"
}