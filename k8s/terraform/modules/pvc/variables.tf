variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "name" {
  description = "PVC name"
  type        = string
}

variable "size" {
  description = "Storage size for PVC"
  type        = string
}

variable "storage_class" {
  description = "Storage class for PVC"
  type        = string
  default     = "standard"
}