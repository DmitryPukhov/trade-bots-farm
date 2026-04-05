output "service_host" {
  value       = helm_release.grafana.values["service.host"]
  description = "Grafana service host"
}

output "service_port" {
  value       = helm_release.grafana.values["service.port"]
  description = "Grafana service port"
}