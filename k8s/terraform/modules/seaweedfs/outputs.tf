output "service_host" {
  value       = var.enabled ? "seaweedfs-s3.${var.namespace}.svc.cluster.local" : ""
  description = "SeaweedFS S3 API service host"
}

output "service_port" {
  value       = var.enabled ? var.s3_port : 0
  description = "SeaweedFS S3 API service port"
}

output "filer_host" {
  value       = var.enabled ? "seaweedfs-filer.${var.namespace}.svc.cluster.local" : ""
  description = "SeaweedFS Filer service host"
}

output "filer_port" {
  value       = var.enabled ? 8888 : 0
  description = "SeaweedFS Filer service port"
}

output "master_host" {
  value       = var.enabled ? "seaweedfs-master.${var.namespace}.svc.cluster.local" : ""
  description = "SeaweedFS Master service host"
}

output "master_port" {
  value       = var.enabled ? 9333 : 0
  description = "SeaweedFS Master service port"
}

output "s3_endpoint" {
  value       = var.enabled ? "http://seaweedfs-s3.${var.namespace}.svc.cluster.local:${var.s3_port}" : ""
  description = "SeaweedFS S3 API endpoint"
}

output "s3_endpoint_external" {
  value       = var.enabled ? "http://seaweedfs-s3.${var.namespace}.svc.cluster.local:${var.s3_port}" : ""
  description = "SeaweedFS S3 API external endpoint"
}

output "ingress_url" {
  value       = var.enabled && var.ingress_enabled && (var.ingress_host != "" || var.s3_ingress_host != "") ? "http://${var.s3_ingress_host != "" ? var.s3_ingress_host : var.ingress_host}" : ""
  description = "SeaweedFS S3 API external URL via Ingress"
}

output "master_ingress_url" {
  value       = var.enabled && var.ingress_enabled && (var.ingress_host != "" || var.master_ingress_host != "") ? "http://${var.master_ingress_host != "" ? var.master_ingress_host : var.ingress_host}" : ""
  description = "SeaweedFS Master Web UI external URL via Ingress"
}

output "filer_ingress_url" {
  value       = var.enabled && var.ingress_enabled && (var.ingress_host != "" || var.filer_ingress_host != "") ? "http://${var.filer_ingress_host != "" ? var.filer_ingress_host : var.ingress_host}" : ""
  description = "SeaweedFS Filer Web UI external URL via Ingress"
}


output "access_key" {
  value       = var.enabled ? var.s3_access_key : ""
  description = "SeaweedFS S3 access key"
  sensitive   = true
}

output "secret_key" {
  value       = var.enabled ? var.s3_secret_key : ""
  description = "SeaweedFS S3 secret key"
  sensitive   = true
}

output "default_bucket_name" {
  value       = var.enabled ? var.default_bucket_name : ""
  description = "Default bucket name"
}

output "s3_ingress_host" {
  value       = var.enabled && var.ingress_enabled ? (var.s3_ingress_host != "" ? var.s3_ingress_host : var.ingress_host) : ""
  description = "S3 API ingress host"
}

output "filer_ingress_host" {
  value       = var.enabled && var.ingress_enabled ? (var.filer_ingress_host != "" ? var.filer_ingress_host : var.ingress_host) : ""
  description = "Filer UI ingress host"
}

output "master_ingress_host" {
  value       = var.enabled && var.ingress_enabled ? (var.master_ingress_host != "" ? var.master_ingress_host : var.ingress_host) : ""
  description = "Master UI ingress host"
}

output "operator_namespace" {
  value       = var.enabled ? var.namespace : ""
  description = "Kubernetes namespace where SeaweedFS operator is deployed"
}

output "cluster_name" {
  value       = var.enabled ? "seaweedfs" : ""
  description = "SeaweedFS cluster name"
}
