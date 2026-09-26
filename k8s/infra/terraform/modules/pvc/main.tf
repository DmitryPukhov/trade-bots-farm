resource "kubernetes_persistent_volume_claim" "pvc" {
  metadata {
    name = var.name
    namespace = var.namespace
  }

  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = var.storage_class
    resources {
      requests = {
        storage = var.size
      }
    }
  }
}