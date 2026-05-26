variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "enabled" {
  description = "Whether to enable Kafka deployment"
  type        = bool
  default     = true
}

variable "ingress_enabled" {
  description = "Whether to use Ingress for external Kafka listener instead of NodePort"
  type        = bool
  default     = false
}

variable "ingress_host" {
  description = "Hostname for the Kafka external bootstrap Ingress"
  type        = string
  default     = ""
}

variable "ingress_class" {
  description = "Ingress class for the Kafka external listener (e.g., nginx)"
  type        = string
  default     = "nginx"
}
