variable "namespace" {
  description = "Kubernetes namespace for all resources"
  type        = string
  default     = "trade-bots-farm"
}

variable "docker_registry" {
  description = "Docker registry URL"
  type        = string
  default     = "$(minikube ip):30500"
}


variable "enable_seaweedfs" {
  description = "Enable SeaweedFS deployment"
  type        = bool
  default     = true
}

variable "enable_mlflow" {
  description = "Enable MLflow deployment"
  type        = bool
  default     = true
}

variable "enable_prometheus" {
  description = "Enable Prometheus deployment"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana deployment"
  type        = bool
  default     = true
}

variable "enable_kafka" {
  description = "Enable Kafka/Strimzi deployment"
  type        = bool
  default     = true
}

variable "enable_kafka_ui" {
  description = "Enable Kafka UI deployment"
  type        = bool
  default     = true
}

variable "enable_kafka_connect" {
  description = "Enable Kafka Connect deployment"
  type        = bool
  default     = true
}

variable "enable_airflow" {
  description = "Enable Airflow deployment"
  type        = bool
  default     = true
}

variable "enable_registry" {
  description = "Enable Docker registry deployment"
  type        = bool
  default     = true
}

variable "enable_secrets" {
  description = "Enable secrets deployment"
  type        = bool
  default     = true
}

variable "secret_values" {
  description = "Map of secret names to maps of placeholder values for secret definitions."
  type        = map(map(string))
  default     = {}
}

variable "seaweedfs_ingress_enabled" {
  description = "Enable Ingress for SeaweedFS S3 API"
  type        = bool
  default     = true
}

variable "seaweedfs_ingress_host" {
  description = "Hostname for SeaweedFS Ingress (e.g., seaweedfs.tradebotsfarm.cluster.local)"
  type        = string
  default     = "seaweedfs.tradebotsfarm.svc.cluster.local"
}

variable "seaweedfs_s3_ingress_host" {
  description = "Hostname for SeaweedFS S3 API ingress (e.g., s3.tradebotsfarm.svc.cluster.local). If empty, will use seaweedfs_ingress_host."
  type        = string
  default     = ""
}

variable "seaweedfs_filer_ingress_host" {
  description = "Hostname for SeaweedFS Filer UI ingress (e.g., filer.tradebotsfarm.svc.cluster.local). If empty, will use seaweedfs_ingress_host."
  type        = string
  default     = ""
}

variable "seaweedfs_master_ingress_host" {
  description = "Hostname for SeaweedFS Master UI ingress (e.g., master.tradebotsfarm.svc.cluster.local). If empty, will use seaweedfs_ingress_host."
  type        = string
  default     = ""
}

variable "seaweedfs_webui_auth_enabled" {
  description = "Whether to enable basic authentication for SeaweedFS web UI ingresses (master, filer, volume)."
  type        = bool
  default     = false
}

variable "seaweedfs_webui_auth_username" {
  description = "Username for basic authentication."
  type        = string
  default     = "admin"
}

variable "seaweedfs_webui_auth_password" {
  description = "Password for basic authentication."
  type        = string
  default     = ""
  sensitive   = true
}

variable "seaweedfs_webui_auth_secret_name" {
  description = "Name of an existing Kubernetes secret containing basic auth credentials (key 'auth' with htpasswd format). If provided, the module will use this secret instead of creating a new one."
  type        = string
  default     = ""
}

variable "seaweedfs_webui_auth_secret_namespace" {
  description = "Namespace of the existing basic auth secret. Defaults to var.namespace."
  type        = string
  default     = ""
}

variable "seaweedfs_create_webui_auth_secret" {
  description = "Whether to create a Kubernetes secret for basic auth credentials. If false, you must provide an existing secret via seaweedfs_webui_auth_secret_name."
  type        = bool
  default     = false
}

variable "seaweedfs_s3_access_key" {
  description = "S3 access key for SeaweedFS authentication. Should be set via environment variable TF_VAR_seaweedfs_s3_access_key."
  type        = string
  default     = ""
  sensitive   = true
}

variable "seaweedfs_s3_secret_key" {
  description = "S3 secret key for SeaweedFS authentication. Should be set via environment variable TF_VAR_seaweedfs_s3_secret_key."
  type        = string
  default     = ""
  sensitive   = true
}

variable "seaweedfs_s3_credentials_secret_name" {
  description = "Name of an existing Kubernetes secret containing S3 credentials (keys: access_key, secret_key). If provided, the module will use this secret instead of creating a new one. If not provided, the module will create a secret using seaweedfs_s3_access_key and seaweedfs_s3_secret_key."
  type        = string
  default     = ""
}

variable "seaweedfs_create_s3_credentials_secret" {
  description = "Whether to create a Kubernetes secret for S3 credentials. If false, you must provide an existing secret via seaweedfs_s3_credentials_secret_name."
  type        = bool
  default     = true
}