output "webserver_host" {
  value       = helm_release.airflow.values["webserver.service.host"]
  description = "Airflow webserver host"
}

output "webserver_port" {
  value       = helm_release.airflow.values["webserver.service.port"]
  description = "Airflow webserver port"
}