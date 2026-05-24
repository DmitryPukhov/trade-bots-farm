variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "enabled" {
  description = "Whether to enable MLflow deployment"
  type        = bool
  default     = true
}

variable "ingress_enabled" {
  description = "Whether to create an Ingress resource for MLflow"
  type        = bool
  default     = false
}

variable "ingress_host" {
  description = "Hostname for the MLflow Ingress"
  type        = string
  default     = "mlflow.tradebotsfarm.svc.cluster.local"
}

variable "ingress_class" {
  description = "Ingress class (e.g., nginx)"
  type        = string
  default     = "nginx"
}
