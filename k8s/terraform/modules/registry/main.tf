resource "kubernetes_persistent_volume" "registry" {
  metadata {
    name = "registry-pv"
  }

  spec {
    capacity = {
      storage = "10Gi"
    }
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = "standard"

    host_path {
      path = "/data/registry"
      type = "DirectoryOrCreate"
    }
  }
}

resource "kubernetes_persistent_volume_claim" "registry" {
  metadata {
    name = "registry-pvc"
    namespace = var.namespace
  }

  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = "standard"
    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "registry" {
  metadata {
    name = "registry"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "registry"
      }
    }

    template {
      metadata {
        labels = {
          app = "registry"
        }
      }

      spec {
        container {
          name  = "registry"
          image = "registry:2"

          port {
            container_port = 5000
          }

          volume_mount {
            name       = "registry-storage"
            mount_path = "/var/lib/registry"
          }
        }

        volume {
          name = "registry-storage"
          persistent_volume_claim {
            claim_ref {
              name = "registry-pvc"
              namespace = var.namespace
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "registry" {
  metadata {
    name = "registry"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "registry"
    }
    port {
      port        = 5000
      target_port = 5000
    }
    type = "NodePort"
  }
}

resource "null_resource" "copy_certs" {
  provisioner "local-exec" {
    command = "echo 'Copying Docker registry certs to Minikube...'; \
              DOCKER_REGISTRY=$(minikube ip):30500; \
              mkdir -p /tmp/certs; \
              cp ../../secret/registry/tls.crt /tmp/certs/ca.crt; \
              minikube ssh \"sudo mkdir -p /etc/docker/certs.d/${DOCKER_REGISTRY}\"; \
              minikube cp /tmp/certs/ca.crt ${DOCKER_REGISTRY}/ca.crt; \
              rm -rf /tmp/certs"
  }

  depends_on = [
    resource.kubernetes_deployment.registry
  ]
}