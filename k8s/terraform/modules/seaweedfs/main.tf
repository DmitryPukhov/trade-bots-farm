# Add SeaweedFS Helm repository
resource "null_resource" "add_helm_repo" {
  count = var.enabled ? 1 : 0

  provisioner "local-exec" {
    command = "helm repo add seaweedfs https://seaweedfs.github.io/seaweedfs/helm && helm repo update seaweedfs"
  }
}

# Install SeaweedFS using local-exec and helm CLI
resource "null_resource" "install_seaweedfs" {
  count = var.enabled ? 1 : 0

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


  