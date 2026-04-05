resource "kubernetes_manifest" "strimzi_operator" {
  manifest = yamldecode(templatefile("../../kafka/strimzi-operator.yaml.tpl", {
    namespace = var.namespace
  }))
}

resource "kubernetes_manifest" "kafka_cluster" {
  manifest = yamldecode(file("../../kafka/values.yaml"))

  depends_on = [
    resource.kubernetes_manifest.strimzi_operator
  ]
}