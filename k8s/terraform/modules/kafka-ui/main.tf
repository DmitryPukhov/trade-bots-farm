resource "helm_release" "kafka_ui" {
  name       = "kafka-ui"
  repository = "https://provectus.github.io/kafka-ui-charts"
  chart      = "kafka-ui"
  version    = "0.7.6"
  namespace  = var.namespace
  values = [
    file("${path.module}/values.yaml")
  ]

  # Ingress configuration
  # NOTE: This chart uses scalar values (ingress.host, ingress.path, ingress.pathType),
  # NOT array-based paths like ingress.hosts[0].host
  set {
    name  = "ingress.enabled"
    value = var.ingress_enabled
  }

  set {
    name  = "ingress.className"
    value = var.ingress_class
  }

  set {
    name  = "ingress.host"
    value = var.ingress_host
  }

  set {
    name  = "ingress.path"
    value = "/"
  }

  set {
    name  = "ingress.pathType"
    value = "Prefix"
  }

  # Switch service to ClusterIP when ingress is enabled
  set {
    name  = "service.type"
    value = var.ingress_enabled ? "ClusterIP" : "NodePort"
  }
}