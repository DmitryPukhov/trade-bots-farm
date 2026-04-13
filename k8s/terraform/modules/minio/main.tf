resource "helm_release" "minio" {
  count      = var.enabled ? 1 : 0
  name       = "minio"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "minio"
  version    = "14.10.0"
  namespace  = var.namespace
  values = [
    file("${path.module}/values.yaml")
  ]

  set {
    name  = "service.host"
    value = "minio.${var.namespace}.svc.cluster.local"
  }

  set {
    name  = "service.port"
    value = 80
  }

  depends_on = [
    module.pvc_minio
  ]
}

module "pvc_minio" {
  source    = "../pvc"
  namespace = var.namespace
  name      = "minio"
  size      = "10Gi"
  storage_class = "standard"
  count     = var.enabled ? 1 : 0
}