output "webserver_host" {
  value       = var.enabled ? "airflow-webserver.${var.namespace}.svc.cluster.local" : ""
  description = "Airflow webserver host"
}

output "webserver_port" {
  value       = var.enabled ? 8080 : 0
  description = "Airflow webserver port"
}