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

data "kubernetes_namespace" "current" {
  metadata {
    name = var.namespace
  }
}

# Module for secrets
terraform {
  required_version = ">= 1.0"
}

module "secrets" {
  source    = "./modules/secrets"
  namespace = var.namespace

  depends_on = [
    data.kubernetes_namespace.current
  ]
}

# Module for MinIO
terraform {
  required_version = ">= 1.0"
}

module "minio" {
  source    = "./modules/minio"
  namespace = var.namespace

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
  enabled   = var.enable_mlflow

  depends_on = [
    module.minio
  ]
}

# Module for Prometheus
terraform {
  required_version = ">= 1.0"
}

module "prometheus" {
  source    = "./modules/prometheus"
  namespace = var.namespace

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

  depends_on = [
    module.kafka
  ]
}

# Module for Kafka Connect
terraform {
  required_version = ">= 1.0"
}

module "kafka_connect" {
  source        = "./modules/kafka-connect"
  namespace     = var.namespace
  docker_registry = var.docker_registry
  enabled       = var.enable_kafka_connect

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

  depends_on = [
    module.airflow
  ]
}