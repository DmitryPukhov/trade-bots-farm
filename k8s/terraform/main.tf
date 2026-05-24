terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.3"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

# Namespace resource
terraform {
  required_version = ">= 1.0"
}

resource "kubernetes_namespace" "current" {
  metadata {
    name = var.namespace
  }
}

# Module for secrets
terraform {
  required_version = ">= 1.0"
}

module "secrets" {
  source        = "./modules/secrets"
  namespace     = var.namespace
  secret_values = var.secret_values
  count         = var.enable_secrets ? 1 : 0

  depends_on = [
    kubernetes_namespace.current
  ]
}

# Module for SeaweedFS
terraform {
  required_version = ">= 1.0"
}

locals {
  # Read S3 credentials from the seaweedfs-s3-credentials.yaml secret file
  # This ensures the YAML-stored keys are passed to Helm's --set s3.credentials.admin.*
  # and to the IAM config job, instead of falling back to the default "minioadmin".
  seaweedfs_s3_secret_raw = yamldecode(file("${path.module}/secrets/seaweedfs-s3-credentials.yaml"))
  seaweedfs_s3_access_key = try(local.seaweedfs_s3_secret_raw.stringData.access_key, var.seaweedfs_s3_access_key)
  seaweedfs_s3_secret_key = try(local.seaweedfs_s3_secret_raw.stringData.secret_key, var.seaweedfs_s3_secret_key)
}

module "seaweedfs" {
  source    = "./modules/seaweedfs"
  namespace = var.namespace
  count     = var.enable_seaweedfs ? 1 : 0

  ingress_enabled = var.seaweedfs_ingress_enabled
  ingress_host    = var.seaweedfs_ingress_host

  s3_ingress_host     = var.seaweedfs_s3_ingress_host
  filer_ingress_host  = var.seaweedfs_filer_ingress_host
  master_ingress_host = var.seaweedfs_master_ingress_host

  webui_auth_enabled          = var.seaweedfs_webui_auth_enabled
  webui_auth_username         = var.seaweedfs_webui_auth_username
  webui_auth_password         = var.seaweedfs_webui_auth_password
  webui_auth_secret_name      = var.seaweedfs_webui_auth_secret_name
  webui_auth_secret_namespace = var.seaweedfs_webui_auth_secret_namespace
  create_webui_auth_secret    = var.seaweedfs_create_webui_auth_secret

  s3_access_key                = local.seaweedfs_s3_access_key
  s3_secret_key                = local.seaweedfs_s3_secret_key
  s3_credentials_secret_name   = var.seaweedfs_s3_credentials_secret_name
  create_s3_credentials_secret = var.seaweedfs_create_s3_credentials_secret
  configure_iam_credentials    = false

  depends_on = [
    module.secrets
  ]
}

# Module for MLflow
terraform {
  required_version = ">= 1.0"
}

module "mlflow" {
  source    = "./modules/mlflow"
  namespace = var.namespace
  count     = var.enable_mlflow ? 1 : 0

  depends_on = [
    module.seaweedfs
  ]
}

# Module for Prometheus
terraform {
  required_version = ">= 1.0"
}

module "prometheus" {
  source    = "./modules/prometheus"
  namespace = var.namespace
  count     = var.enable_prometheus ? 1 : 0

  depends_on = [
    module.mlflow
  ]
}

# Module for Grafana
terraform {
  required_version = ">= 1.0"
}

module "grafana" {
  source    = "./modules/grafana"
  namespace = var.namespace
  count     = var.enable_grafana ? 1 : 0

  depends_on = [
    module.prometheus
  ]
}

# Module for Kafka
terraform {
  required_version = ">= 1.0"
}

module "kafka" {
  source    = "./modules/kafka"
  namespace = var.namespace
  count     = var.enable_kafka ? 1 : 0

  depends_on = [
    module.grafana
  ]
}

# Module for Kafka UI
terraform {
  required_version = ">= 1.0"
}

module "kafka_ui" {
  source    = "./modules/kafka-ui"
  namespace = var.namespace
  count     = var.enable_kafka_ui ? 1 : 0

  depends_on = [
    module.kafka
  ]
}

# Module for Kafka Connect
terraform {
  required_version = ">= 1.0"
}

module "kafka_connect" {
  source          = "./modules/kafka-connect"
  namespace       = var.namespace
  docker_registry = var.docker_registry
  count           = var.enable_kafka_connect ? 1 : 0

  depends_on = [
    module.kafka_ui
  ]
}

# Module for Airflow
terraform {
  required_version = ">= 1.0"
}

module "airflow" {
  source    = "./modules/airflow"
  namespace = var.namespace
  count     = var.enable_airflow ? 1 : 0

  depends_on = [
    module.kafka_connect
  ]
}

# Module for Registry
terraform {
  required_version = ">= 1.0"
}

module "registry" {
  source    = "./modules/registry"
  namespace = var.namespace
  count     = var.enable_registry ? 1 : 0

  depends_on = [
    module.airflow
  ]
}