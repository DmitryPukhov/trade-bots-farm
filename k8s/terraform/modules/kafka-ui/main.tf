resource "helm_release" "kafka_ui" {
  name       = "kafka-ui"
  repository = "https://provectus.github.io/kafka-ui-charts"
  chart      = "kafka-ui"
  version    = "1.1.2"
  namespace  = var.namespace
  values = [
    file("${path.module}/values.yaml")
  ]
}