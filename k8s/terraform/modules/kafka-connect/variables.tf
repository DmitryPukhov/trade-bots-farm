variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "docker_registry" {
  description = "Docker registry URL"
  type        = string
}

variable "enabled" {
  description = "Whether to enable the Kafka Connect module"
  type        = bool
  default     = true
}