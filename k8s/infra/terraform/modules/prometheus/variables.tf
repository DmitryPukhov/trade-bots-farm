variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "enabled" {
  description = "Whether to enable Prometheus deployment"
  type        = bool
  default     = true
}

variable "ingress_enabled" {
  description = "Whether to create an Ingress resource for Prometheus"
  type        = bool
  default     = false
}

variable "ingress_host" {
  description = "Hostname for the Prometheus Ingress"
  type        = string
  default     = "prometheus.tradebotsfarm.svc.cluster.local"
}

variable "ingress_class" {
  description = "Ingress class (e.g., nginx)"
  type        = string
  default     = "nginx"
}
