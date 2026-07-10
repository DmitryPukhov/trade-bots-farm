resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  version    = "27.1.0"
  namespace  = var.namespace
  values = [
    file("${path.module}/values.yaml")
  ]
  set {
    name  = "serviceMonitor.enabled"
    value = "true"
  }
}

resource "helm_release" "prometheus_pushgateway" {
  name       = "prometheus-pushgateway"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus-pushgateway"
  version    = "3.6.0"
  namespace  = var.namespace
  values = [
    file("${path.module}/prometheus-pushgateway.values.yaml")
  ]
}