output "namespace" {
  value       = var.namespace
  description = "Kubernetes namespace for all resources"
}

output "secrets" {
  value       = length(module.secrets) > 0 ? "Secrets created: ${join(", ", module.secrets[0].secret_names)}" : ""
  description = "Secrets"
  depends_on  = [module.seaweedfs]
}

output "docker_registry" {
  value       = var.docker_registry
  description = "Docker registry URL"
}


output "mlflow_tracking_uri" {
  value       = length(module.mlflow) > 0 ? "http://${module.mlflow[0].service_host}:${module.mlflow[0].service_port}" : ""
  description = "MLflow tracking URI"
  depends_on  = [module.mlflow]
}

output "prometheus_url" {
  value       = length(module.prometheus) > 0 ? "http://${module.prometheus[0].service_host}:${module.prometheus[0].service_port}" : ""
  description = "Prometheus web UI URL"
  depends_on  = [module.prometheus]
}

output "grafana_url" {
  value       = length(module.grafana) > 0 ? "http://${module.grafana[0].service_host}:${module.grafana[0].service_port}" : ""
  description = "Grafana web UI URL"
  depends_on  = [module.grafana]
}

output "kafka_bootstrap_servers" {
  value       = length(module.kafka) > 0 ? module.kafka[0].bootstrap_servers : ""
  description = "Kafka bootstrap servers (internal, plaintext)"
  depends_on  = [module.kafka]
}

output "kafka_external_bootstrap_servers" {
  value       = length(module.kafka) > 0 ? module.kafka[0].external_bootstrap_servers : ""
  description = "Kafka bootstrap servers for external clients (ingress:443 or nodeport:9094)"
  depends_on  = [module.kafka]
}

output "kafka_ui_url" {
  value       = length(module.kafka_ui) > 0 ? "http://${module.kafka_ui[0].service_host}:${module.kafka_ui[0].service_port}" : ""
  description = "Kafka UI URL"
  depends_on  = [module.kafka_ui]
}

output "airflow_webserver_url" {
  value       = length(module.airflow) > 0 ? "http://${module.airflow[0].webserver_host}:${module.airflow[0].webserver_port}" : ""
  description = "Airflow webserver URL"
  depends_on  = [module.airflow]
}