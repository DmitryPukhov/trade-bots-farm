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

  # Ingress configuration
  set {
    name  = "server.ingress.enabled"
    value = var.ingress_enabled
  }

  set {
    name  = "server.ingress.ingressClassName"
    value = var.ingress_class
  }

  set {
    name  = "server.ingress.hosts[0]"
    value = var.ingress_host
  }

  # Switch service to ClusterIP when ingress is enabled
  set {
    name  = "server.service.type"
    value = var.ingress_enabled ? "ClusterIP" : "NodePort"
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