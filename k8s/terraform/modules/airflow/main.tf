resource "helm_release" "airflow" {
  name       = "airflow"
  repository = "https://airflow.apache.org"
  chart      = "airflow"
  version    = "1.7.0"
  namespace  = var.namespace
  values = [
    file("../../airflow/values.yaml")
  ]
  timeout = 1200

  depends_on = [
    module.pvc_airflow_dags,
    module.pvc_environment,
    module.pvc_wheels
  ]
}

module "pvc_airflow_dags" {
  source    = "../pvc"
  namespace = var.namespace
  name      = "airflow-dags"
  size      = "5Gi"
  storage_class = "standard"
}

module "pvc_environment" {
  source    = "../pvc"
  namespace = var.namespace
  name      = "environment"
  size      = "5Gi"
  storage_class = "standard"
}

module "pvc_wheels" {
  source    = "../pvc"
  namespace = var.namespace
  name      = "wheels"
  size      = "5Gi"
  storage_class = "standard"
}