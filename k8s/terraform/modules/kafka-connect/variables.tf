variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "docker_registry" {
  description = "Docker registry URL"
  type        = string
}