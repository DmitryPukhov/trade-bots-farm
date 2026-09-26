resource "helm_release" "grafana" {
  name       = "grafana"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "grafana"
  version    = "10.1.1"
  namespace  = var.namespace
  values = [
    file("${path.module}/values.yaml")
  ]

  depends_on = [
    module.pvc_grafana
  ]
}

module "pvc_grafana" {
  source    = "../pvc"
  namespace = var.namespace
  name      = "grafana"
  size      = "10Gi"
  storage_class = "standard"
}