resource "helm_release" "airflow" {
  name       = "airflow"
  repository = "https://airflow.apache.org"
  chart      = "airflow"
  version    = "1.7.0"
  namespace  = var.namespace
  values = [
    file("${path.module}/values.yaml")
  ]
  timeout = 1200


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

resource "null_resource" "cleanup_airflow" {
  provisioner "local-exec" {
    command = <<EOT
set +e
echo 'Cleaning up old Airflow resources...'
for pvc in $(kubectl get pvc --no-headers | grep -E 'airflow|environment|wheels' | awk '{print $1}'); do
  echo "Force deleting PVC: $pvc"
  kubectl patch pvc "$pvc" -p '{"metadata":{"finalizers":null}}'
  kubectl delete --force pvc "$pvc"
done
sleep 5
for pv in $(kubectl get pv --no-headers | grep -E 'airflow|environment|wheels' | awk '{print $1}'); do
  echo "Force deleting PV: $pv"
  kubectl patch pv "$pv" -p '{"metadata":{"finalizers":null}}'
  kubectl delete --force pv "$pv"
done
for name in $(kubectl get statefulset | grep airflow | awk '{print $1}'); do
  echo "Deleting statefulset $name"
  kubectl delete statefulset $name
done
set -e
EOT
  }

  triggers = {
    namespace = var.namespace
  }
}

