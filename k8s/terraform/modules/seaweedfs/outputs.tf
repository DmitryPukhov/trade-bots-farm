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

output "operator_namespace" {
  value       = var.enabled ? var.namespace : ""
  description = "Kubernetes namespace where SeaweedFS operator is deployed"
}

output "cluster_name" {
  value       = var.enabled ? "seaweedfs" : ""
  description = "SeaweedFS cluster name"
}
