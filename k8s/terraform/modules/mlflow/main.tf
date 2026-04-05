resource "helm_release" "mlflow" {
  name       = "mlflow"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "mlflow"
  version    = "10.1.3"
  namespace  = var.namespace
  values = [
    file("../../mlflow/values.yaml")
  ]

  depends_on = [
    module.pvc_mlflow_tracking,
    module.pvc_mlflow_postgresql
  ]
}

module "pvc_mlflow_tracking" {
  source    = "../pvc"
  namespace = var.namespace
  name      = "mlflow-tracking"
  size      = "10Gi"
  storage_class = "standard"
}

module "pvc_mlflow_postgresql" {
  source    = "../pvc"
  namespace = var.namespace
  name      = "data-mlflow-postgresql-0"
  size      = "10Gi"
  storage_class = "standard"
}