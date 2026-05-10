# Add SeaweedFS Helm repository
locals {
  values_hash = filebase64sha256("${path.module}/values.yaml")
  install_triggers = {
    namespace       = var.namespace
    master_replicas = var.master_replicas
    volume_replicas = var.volume_replicas
    s3_port         = var.s3_port
    volume_size     = var.volume_size
    storage_class   = var.storage_class
    values_hash     = local.values_hash
    s3_host         = local.s3_host
    filer_host      = local.filer_host
    master_host     = local.master_host
    volume_host     = local.volume_host
    ingress_enabled = var.ingress_enabled
  }

  # Compute ingress hosts
  s3_host     = var.s3_ingress_host != "" ? var.s3_ingress_host : var.ingress_host
  filer_host  = var.filer_ingress_host != "" ? var.filer_ingress_host : var.ingress_host
  master_host = var.master_ingress_host != "" ? var.master_ingress_host : var.ingress_host
  volume_host = var.ingress_host

  # Build extra --set flags for ingress hosts if ingress enabled
  ingress_host_flags = var.ingress_enabled ? join(" ", [
    for flag in [
      local.s3_host != "" ? "--set s3.ingress.host=${local.s3_host}" : "",
      local.filer_host != "" ? "--set filer.ingress.host=${local.filer_host}" : "",
      local.master_host != "" ? "--set master.ingress.host=${local.master_host}" : "",
      local.volume_host != "" ? "--set volume.ingress.host=${local.volume_host}" : "",
    ] : flag if flag != ""
  ]) : ""

  # Build extra --set flags for S3 credentials and security
  s3_credentials_flags = var.enabled ? join(" ", [
    for flag in [
      var.s3_access_key != "" ? "--set s3.credentials.admin.accessKey=${var.s3_access_key}" : "",
      var.s3_secret_key != "" ? "--set s3.credentials.admin.secretKey=${var.s3_secret_key}" : "",
      "--set s3.enableAuth=true",
    ] : flag if flag != ""
  ]) : ""

  # Determine secret name for S3 credentials
  s3_credentials_secret_name_final = var.s3_credentials_secret_name != "" ? var.s3_credentials_secret_name : "seaweedfs-s3-credentials"
}

resource "null_resource" "add_helm_repo" {
  count = var.enabled ? 1 : 0

  triggers = {
    enabled = var.enabled
    repo    = "seaweedfs"
  }

  provisioner "local-exec" {
    command = "helm repo add seaweedfs https://seaweedfs.github.io/seaweedfs/helm && helm repo update seaweedfs"
  }
}

# Install SeaweedFS using local-exec and helm CLI
resource "null_resource" "install_seaweedfs" {
  count = var.enabled ? 1 : 0

  triggers = local.install_triggers

  provisioner "local-exec" {
    command = <<-EOT
      helm upgrade --install seaweedfs seaweedfs/seaweedfs \
        --namespace ${var.namespace} \
        --version 4.21.0 \
        --values ${path.module}/values.yaml \
        --set global.imageRegistry="" \
        --set global.repository="" \
        --set global.imageName="chrislusf/seaweedfs" \
        --set master.replicas=${var.master_replicas} \
        --set volume.replicas=${var.volume_replicas} \
        --set filer.s3.port=${var.s3_port} \
        --set volume.size=${var.volume_size} \
        --set volume.storageClass=${var.storage_class} \
        ${local.ingress_host_flags} \
        ${local.s3_credentials_flags} \
        --debug
    EOT
  }

  depends_on = [null_resource.add_helm_repo]
}

# Wait for SeaweedFS to be fully ready
resource "time_sleep" "wait_for_seaweedfs" {
  count = var.enabled ? 1 : 0

  depends_on      = [null_resource.install_seaweedfs]
  create_duration = "60s"
}
# Create SeaweedFS S3 credentials secret
resource "kubernetes_secret" "seaweedfs_s3_credentials" {
  count = var.enabled && var.create_s3_credentials_secret ? 1 : 0

  metadata {
    name      = local.s3_credentials_secret_name_final
    namespace = var.namespace
  }

  data = {
    access_key = var.s3_access_key
    secret_key = var.s3_secret_key
  }

  type = "Opaque"

  depends_on = [null_resource.install_seaweedfs]
}

# Create default bucket using a Kubernetes Job
resource "kubernetes_job" "create_default_bucket" {
  count = var.enabled && var.create_default_bucket ? 1 : 0

  metadata {
    name      = "create-default-bucket"
    namespace = var.namespace
  }

  spec {
    template {
      metadata {
        name = "create-default-bucket"
      }
      spec {
        container {
          name    = "awscli"
          image   = "bitnami/aws-cli:latest"
          command = ["/bin/sh", "-c"]
          args = [
            <<-EOT
              # Wait for S3 service to be reachable
              until curl -f -s http://seaweedfs-s3.${var.namespace}.svc.cluster.local:${var.s3_port}/ > /dev/null 2>&1; do
                echo "Waiting for SeaweedFS S3 API..."
                sleep 5
              done
              # Create bucket if it doesn't exist
              aws --endpoint-url http://seaweedfs-s3.${var.namespace}.svc.cluster.local:${var.s3_port} s3api head-bucket --bucket ${var.default_bucket_name} 2>/dev/null || \
              aws --endpoint-url http://seaweedfs-s3.${var.namespace}.svc.cluster.local:${var.s3_port} s3 mb s3://${var.default_bucket_name}
              echo "Bucket ${var.default_bucket_name} created or already exists"
            EOT
          ]
          env {
            name  = "AWS_ACCESS_KEY_ID"
            value = var.s3_access_key
          }
          env {
            name  = "AWS_SECRET_ACCESS_KEY"
            value = var.s3_secret_key
          }
          env {
            name  = "AWS_DEFAULT_REGION"
            value = "us-east-1"
          }
        }
        restart_policy = "Never"
      }
    }
    backoff_limit = 3
    active_deadline_seconds = 300
  }

  wait_for_completion = false

  depends_on = [time_sleep.wait_for_seaweedfs]
}



  