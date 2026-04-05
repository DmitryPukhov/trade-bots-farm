output "namespace" {
  value       = var.namespace
  description = "Kubernetes namespace for all resources"
}

output "docker_registry" {
  value       = var.docker_registry
  description = "Docker registry URL"
}

output "minio_endpoint" {
  value       = "http://${module.minio.service_host}:${module.minio.service_port}"
  description = "MinIO service endpoint"
  depends_on  = [module.minio]
}

output "mlflow_tracking_uri" {
  value       = "http://${module.mlflow.service_host}:${module.mlflow.service_port}"
  description = "MLflow tracking URI"
  depends_on  = [module.mlflow]
}

output "prometheus_url" {
  value       = "http://${module.prometheus.service_host}:${module.prometheus.service_port}"
  description = "Prometheus web UI URL"
  depends_on  = [module.prometheus]
}

output "grafana_url" {
  value       = "http://${module.grafana.service_host}:${module.grafana.service_port}"
  description = "Grafana web UI URL"
  depends_on  = [module.grafana]
}

output "kafka_bootstrap_servers" {
  value       = module.kafka.bootstrap_servers
  description = "Kafka bootstrap servers"
  depends_on  = [module.kafka]
}

output "kafka_ui_url" {
  value       = "http://${module.kafka_ui.service_host}:${module.kafka_ui.service_port}"
  description = "Kafka UI URL"
  depends_on  = [module.kafka_ui]
}

output "airflow_webserver_url" {
  value       = "http://${module.airflow.webserver_host}:${module.airflow.webserver_port}"
  description = "Airflow webserver URL"
  depends_on  = [module.airflow]
}