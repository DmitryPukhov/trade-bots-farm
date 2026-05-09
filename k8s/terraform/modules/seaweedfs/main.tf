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
      --version 4.0.413 \
      --values ${path.module}/values.yaml \
      --set global.imageRegistry="" \
      --set global.repository="chrislusf" \
      --set global.imageName="seaweedfs" \
      --set master.replicas=${var.master_replicas} \
      --set volume.replicas=${var.volume_replicas} \
      --set filer.enabled=true \
      --set filer.s3.enabled=true \
      --set filer.s3.port=${var.s3_port} \
      --set filer.extraArgs[0]="-s3" \
      --set filer.extraArgs[1]="-s3.port=${var.s3_port}" \
      --set s3.enabled=true \
      --set s3.port=${var.s3_port} \
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

# Create default bucket using a Job
resource "kubernetes_job_v1" "create_bucket" {
  count = var.enabled && var.create_default_bucket ? 1 : 0

  metadata {
    name      = "seaweedfs-create-bucket"
    namespace = var.namespace
  }

  spec {
    template {
      metadata {
        labels = {
          app = "seaweedfs-bucket-creator"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.bucket_creator[0].metadata[0].name

        container {
          name  = "bucket-creator"
          image = "curlimages/curl:latest"

          command = [
            "/bin/sh",
            "-c",
            "curl -X PUT http://s3.${var.namespace}.svc.cluster.local:${var.s3_port}/${var.default_bucket_name} || true"
          ]

          env {
            name  = "AWS_ACCESS_KEY_ID"
            value = var.s3_access_key
          }

          env {
            name  = "AWS_SECRET_ACCESS_KEY"
            value = var.s3_secret_key
          }
        }

        restart_policy = "Never"
      }
    }

    backoff_limit = 3
  }

  depends_on = [
    time_sleep.wait_for_seaweedfs
  ]
}

# Service Account for bucket creation job
resource "kubernetes_service_account" "bucket_creator" {
  count = var.enabled && var.create_default_bucket ? 1 : 0

  metadata {
    name      = "seaweedfs-bucket-creator"
    namespace = var.namespace
  }

  depends_on = [null_resource.install_seaweedfs]
}

# Ingress for SeaweedFS S3 API
resource "kubernetes_ingress_v1" "seaweedfs_s3" {
  count = var.enabled && var.ingress_enabled && (var.ingress_host != "" || var.s3_ingress_host != "") ? 1 : 0

  metadata {
    name      = "seaweedfs-s3"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/ingress.class" = var.ingress_class
    }
  }

  spec {
    rule {
      host = var.s3_ingress_host != "" ? var.s3_ingress_host : var.ingress_host
      http {
        path {
          path = "/"
          backend {
            service {
              name = "seaweedfs-s3"
              port {
                number = var.s3_port
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    null_resource.install_seaweedfs,
    time_sleep.wait_for_seaweedfs
  ]
}


# Ingress for SeaweedFS Filer Web UI
resource "kubernetes_ingress_v1" "seaweedfs_filer" {
  count = var.enabled && var.ingress_enabled && (var.ingress_host != "" || var.filer_ingress_host != "") ? 1 : 0

  metadata {
    name      = "seaweedfs-filer"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/ingress.class" = var.ingress_class
    }
  }

  spec {
    rule {
      host = var.filer_ingress_host != "" ? var.filer_ingress_host : var.ingress_host
      http {
        path {
          path = "/"
          backend {
            service {
              name = "seaweedfs-filer"
              port {
                number = 8888
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    null_resource.install_seaweedfs,
    time_sleep.wait_for_seaweedfs
  ]
}

# Ingress for SeaweedFS Master Web UI
resource "kubernetes_ingress_v1" "seaweedfs_master" {
  count = var.enabled && var.ingress_enabled && (var.ingress_host != "" || var.master_ingress_host != "") ? 1 : 0

  metadata {
    name      = "seaweedfs-master"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/ingress.class" = var.ingress_class
    }
  }

  spec {
    rule {
      host = var.master_ingress_host != "" ? var.master_ingress_host : var.ingress_host
      http {
        path {
          path = "/"
          backend {
            service {
              name = "seaweedfs-master"
              port {
                number = 9333
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    null_resource.install_seaweedfs,
    time_sleep.wait_for_seaweedfs
  ]
}
