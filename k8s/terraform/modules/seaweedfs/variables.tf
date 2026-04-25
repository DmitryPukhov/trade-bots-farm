variable "namespace" {
  description = "Kubernetes namespace for SeaweedFS deployment"
  type        = string
  default     = "default"
}

variable "enabled" {
  description = "Whether to enable SeaweedFS deployment"
  type        = bool
  default     = true
}

variable "master_replicas" {
  description = "Number of SeaweedFS master replicas"
  type        = number
  default     = 1
}

variable "volume_replicas" {
  description = "Number of SeaweedFS volume server replicas"
  type        = number
  default     = 1
}

variable "s3_port" {
  description = "Port for SeaweedFS S3 API"
  type        = number
  default     = 8333
}

variable "volume_size" {
  description = "Storage size for volume servers"
  type        = string
  default     = "10Gi"
}

variable "storage_class" {
  description = "Kubernetes storage class for persistent volumes"
  type        = string
  default     = "standard"
}

variable "s3_access_key" {
  description = "S3 access key for SeaweedFS"
  type        = string
  default     = "minioadmin"
  sensitive   = true
}

variable "s3_secret_key" {
  description = "S3 secret key for SeaweedFS"
  type        = string
  default     = "minioadmin"
  sensitive   = true
}

variable "create_default_bucket" {
  description = "Whether to create a default bucket"
  type        = bool
  default     = true
}

variable "default_bucket_name" {
  description = "Name of the default bucket to create"
  type        = string
  default     = "trade-bots-farm"
}
