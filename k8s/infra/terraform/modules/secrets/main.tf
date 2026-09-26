resource "kubernetes_secret" "secrets" {
  for_each = { for file in fileset("${path.module}/../../secrets", "*.yaml") : file => file }

  metadata {
    name      = substr(each.value, 0, length(each.value) - 5) # Remove .yaml extension
    namespace = var.namespace
  }

  # Correctly parse the YAML file as an object and extract .data
  data = {
    for k, v in yamldecode(file("${path.module}/../../secrets/${each.value}")).stringData : k => v
  }

  type = yamldecode(file("${path.module}/../../secrets/${each.value}")).type
}