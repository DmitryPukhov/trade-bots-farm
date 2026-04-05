variable "namespace" {
  description = "Kubernetes namespace for all resources"
  type        = string
  default     = "default"
}

variable "docker_registry" {
  description = "Docker registry URL"
  type        = string
  default     = "$(minikube ip):30500"
}

variable "enable_minio" {
  description = "Enable MinIO deployment"
  type        = bool
  default     = true
}

variable "enable_mlflow" {
  description = "Enable MLflow deployment"
  type        = bool
  default     = true
}

variable "enable_prometheus" {
  description = "Enable Prometheus deployment"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana deployment"
  type        = bool
  default     = true
}

variable "enable_kafka" {
  description = "Enable Kafka/Strimzi deployment"
  type        = bool
  default     = true
}

variable "enable_kafka_ui" {
  description = "Enable Kafka UI deployment"
  type        = bool
  default     = true
}

variable "enable_kafka_connect" {
  description = "Enable Kafka Connect deployment"
  type        = bool
  default     = true
}

variable "enable_airflow" {
  description = "Enable Airflow deployment"
  type        = bool
  default     = true
}

variable "enable_registry" {
  description = "Enable Docker registry deployment"
  type        = bool
  default     = true
}

variable "enable_secrets" {
  description = "Enable secrets deployment"
  type        = bool
  default     = true
}