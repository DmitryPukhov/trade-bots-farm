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

variable "s3_credentials_secret_name" {
  description = "Name of an existing Kubernetes secret containing S3 credentials (keys: access_key, secret_key). If provided, the module will use this secret instead of creating a new one. If not provided, the module will create a secret using s3_access_key and s3_secret_key."
  type        = string
  default     = ""
}

variable "s3_credentials_secret_namespace" {
  description = "Namespace of the existing S3 credentials secret. Defaults to var.namespace."
  type        = string
  default     = ""
}

variable "create_s3_credentials_secret" {
  description = "Whether to create a Kubernetes secret for S3 credentials. If false, you must provide an existing secret via s3_credentials_secret_name."
  type        = bool
  default     = true
}

variable "create_default_bucket" {
  description = "Whether to create a default bucket"
  type        = bool
  default     = true
}

variable "configure_iam_credentials" {
  description = "Whether to configure SeaweedFS IAM credentials (required for S3 authentication)"
  type        = bool
  default     = true
}

variable "default_bucket_name" {
  description = "Name of the default bucket to create"
  type        = string
  default     = "trade-bots-farm"
}

variable "ingress_enabled" {
  description = "Whether to create an Ingress resource for SeaweedFS"
  type        = bool
  default     = false
}

variable "ingress_host" {
  description = "Hostname for the Ingress (e.g., seaweedfs.tradebotsfarm.svc.cluster.local)"
  type        = string
  default     = "seaweedfs.tradebotsfarm.svc.cluster.local"
}

variable "ingress_class" {
  description = "Ingress class (e.g., nginx)"
  type        = string
  default     = "nginx"
}

variable "master_ingress_path" {
  description = "Path for master web UI ingress (e.g., /master). If empty, master ingress will not be added."
  type        = string
  default     = "/master"
}

variable "filer_ingress_path" {
  description = "Path for filer web UI ingress (e.g., /filer). If empty, filer ingress will not be added."
  type        = string
  default     = "/filer"
}

variable "s3_ingress_host" {
  description = "Hostname for S3 API ingress (e.g., s3.tradebotsfarm.svc.cluster.local). If empty, will use ingress_host."
  type        = string
  default     = "s3.tradebotsfarm.svc.cluster.local"
}

variable "filer_ingress_host" {
  description = "Hostname for filer web UI ingress (e.g., filer.tradebotsfarm.svc.cluster.local). If empty, will use ingress_host."
  type        = string
  default     = "filer.seaweedfs.tradebotsfarm.svc.cluster.local"
}

variable "master_ingress_host" {
  description = "Hostname for master web UI ingress (e.g., master.tradebotsfarm.svc.cluster.local). If empty, will use ingress_host."
  type        = string
  default     = "master.seaweedfs.tradebotsfarm.svc.cluster.local"
}

variable "webui_auth_enabled" {
  description = "Whether to enable basic authentication for web UI ingresses (master, filer, volume)."
  type        = bool
  default     = false
}

variable "webui_auth_username" {
  description = "Username for basic authentication."
  type        = string
  default     = "admin"
}

variable "webui_auth_password" {
  description = "Password for basic authentication."
  type        = string
  default     = ""
  sensitive   = true
}

variable "webui_auth_secret_name" {
  description = "Name of an existing Kubernetes secret containing basic auth credentials (key 'auth' with htpasswd format). If provided, the module will use this secret instead of creating a new one."
  type        = string
  default     = ""
}

variable "webui_auth_secret_namespace" {
  description = "Namespace of the existing basic auth secret. Defaults to var.namespace."
  type        = string
  default     = ""
}

variable "create_webui_auth_secret" {
  description = "Whether to create a Kubernetes secret for basic auth credentials. If false, you must provide an existing secret via webui_auth_secret_name."
  type        = bool
  default     = false
}
