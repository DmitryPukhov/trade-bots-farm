resource "helm_release" "minio" {
  name       = "minio"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "minio"
  version    = "14.10.0"
  namespace  = var.namespace
  values = [
    file("../../minio/values.yaml")
  ]

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
}