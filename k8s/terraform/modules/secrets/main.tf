resource "kubernetes_secret" "secrets" {
  for_each = { for file in fileset("../secret", "*.yaml") : file => file }

  metadata {
    name      = substr(each.value, 0, length(each.value) - 5) # Remove .yaml extension
    namespace = var.namespace
  }

  # Correctly parse the YAML file as an object and extract .data
  data = {
    for k, v in yamldecode(file("../secret/${each.value}")).stringData : k => v
  }

  type = yamldecode(file("../secret/${each.value}")).type
}