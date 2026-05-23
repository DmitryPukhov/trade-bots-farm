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
  force_update = true
  cleanup_on_fail = true
  recreate_pods = true

}

resource "kubernetes_job" "airflow_migrations" {
  metadata {
    name      = "airflow-migrations"
    namespace = var.namespace
  }
  spec {
    template {
      metadata {}
      spec {
        container {
          name    = "migrate"
          image   = "apache/airflow:3.2.1"
          command = ["airflow", "db", "migrate"]
          env {
            name  = "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"
            value = "postgresql://postgres:postgres@airflow-postgresql:5432/airflow"
          }
          env {
            name  = "AIRFLOW__CORE__FERNET_KEY"
            value_from {
              secret_key_ref {
                name = "airflow-fernet-key"
                key  = "fernet-key"
              }
            }
          }
          env {
            name  = "AIRFLOW__WEBSERVER__SECRET_KEY"
            value_from {
              secret_key_ref {
                name = "airflow"
                key  = "webserver-secret-key"
              }
            }
          }
        }
        restart_policy = "Never"
      }
    }
    backoff_limit = 4
  }
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

