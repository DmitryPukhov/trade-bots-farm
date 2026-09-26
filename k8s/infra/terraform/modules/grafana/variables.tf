variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "enabled" {
  description = "Whether to enable Grafana deployment"
  type        = bool
  default     = true
}
