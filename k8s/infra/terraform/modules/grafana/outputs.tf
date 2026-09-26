output "service_host" {
  value       = var.enabled ? "grafana.${var.namespace}.svc.cluster.local" : ""
  description = "Grafana service host"
}

output "service_port" {
  value       = var.enabled ? 80 : 0
  description = "Grafana service port"
}