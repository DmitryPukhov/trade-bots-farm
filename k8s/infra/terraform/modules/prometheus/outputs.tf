output "service_host" {
  value       = var.enabled ? "prometheus-server.${var.namespace}.svc.cluster.local" : ""
  description = "Prometheus service host"
}

output "service_port" {
  value       = var.enabled ? 80 : 0
  description = "Prometheus service port"
}