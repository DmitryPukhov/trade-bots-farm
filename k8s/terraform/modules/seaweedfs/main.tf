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
  count = var.enabled ? 1 : 0

  metadata {
    name      = "seaweedfs-s3-credentials"
    namespace = var.namespace
  }

  data = {
    access_key = var.s3_access_key
    secret_key = var.s3_secret_key
  }

  type = "Opaque"

  depends_on = [null_resource.install_seaweedfs]
}


  