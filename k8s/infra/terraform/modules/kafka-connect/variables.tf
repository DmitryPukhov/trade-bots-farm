variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "enabled" {
  description = "Whether to enable Kafka Connect deployment"
  type        = bool
  default     = true
}

variable "bootstrap_servers" {
  description = "Kafka bootstrap servers for the Connect cluster to connect to"
  type        = string
  default     = ""
}