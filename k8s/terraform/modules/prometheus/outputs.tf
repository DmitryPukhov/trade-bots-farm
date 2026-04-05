output "service_host" {
  value       = helm_release.prometheus.values["server.service.host"]
  description = "Prometheus service host"
}

output "service_port" {
  value       = helm_release.prometheus.values["server.service.port"]
  description = "Prometheus service port"
}