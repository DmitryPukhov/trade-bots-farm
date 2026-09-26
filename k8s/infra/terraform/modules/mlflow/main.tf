resource "helm_release" "mlflow" {
  count      = var.enabled ? 1 : 0
  name       = "mlflow"
  repository = "https://community-charts.github.io/helm-charts"
  chart      = "mlflow"
  version    = "1.8.1"
  namespace  = var.namespace
  values = [
    file("${path.module}/values.yaml")
  ]

  # Ingress configuration
  set {
    name  = "ingress.enabled"
    value = var.ingress_enabled
  }

  set {
    name  = "ingress.className"
    value = var.ingress_class
  }

  set {
    name  = "ingress.hosts[0].host"
    value = var.ingress_host
  }

  set {
    name  = "ingress.hosts[0].paths[0].path"
    value = "/"
  }

  set {
    name  = "ingress.hosts[0].paths[0].pathType"
    value = "Prefix"
  }

  # Switch service to ClusterIP when ingress is enabled
  set {
    name  = "service.type"
    value = var.ingress_enabled ? "ClusterIP" : "LoadBalancer"
  }

  depends_on = [
    module.pvc_mlflow_postgresql
  ]
}

# Pre-create the PVC for PostgreSQL data to persist across chart upgrades
# The community chart's bundled bitnami postgresql will use this via existingClaim
module "pvc_mlflow_postgresql" {
  source    = "../pvc"
  namespace = var.namespace
  name      = "data-mlflow-postgresql-0"
  size      = "10Gi"
  storage_class = "standard"
  count     = var.enabled ? 1 : 0
}
