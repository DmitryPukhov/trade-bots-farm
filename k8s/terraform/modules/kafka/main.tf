resource "null_resource" "remove_strimzi" {
  count = var.enabled ? 1 : 0

  provisioner "local-exec" {
    command = <<EOT
set +e
echo '🚀 Starting Strimzi/Kafka uninstall...'
kubectl delete $(kubectl get kafka,kafkatopics,kafkausers,kafkaconnects,kafkabridges,kafkamirrormaker2 -o name -n ${var.namespace} 2>/dev/null) --ignore-not-found
kubectl delete deployment -l app=strimzi -n ${var.namespace} --ignore-not-found
kubectl delete crd -l app=strimzi --ignore-not-found
kubectl delete clusterrolebinding,clusterrole,clusterroles,rolebindings,configmaps -l app=strimzi --ignore-not-found
kubectl delete validatingwebhookconfigurations,mutatingwebhookconfigurations -l app=strimzi --ignore-not-found
kubectl delete serviceaccount -l app=strimzi -n ${var.namespace} --ignore-not-found
kubectl delete pvc -n ${var.namespace} -l app.kubernetes.io/name=kafka --ignore-not-found
kubectl delete pvc -n ${var.namespace} -l app.kubernetes.io/name=zookeeper --ignore-not-found
kubectl get kafka -n ${var.namespace} -o name | xargs -I {} kubectl patch {} -n ${var.namespace} -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl get crd -l app=strimzi -o name | xargs -I {} kubectl patch {} -p '{"metadata":{"finalizers":[]}}' --type=merge
echo '✅ Strimzi/Kafka uninstallation complete!'
set -e
EOT
  }

  triggers = {
    namespace = var.namespace
  }
}

resource "null_resource" "install_strimzi" {
  count = var.enabled ? 1 : 0

  provisioner "local-exec" {
    command = "kubectl create -f https://strimzi.io/install/latest?namespace=${var.namespace} -n ${var.namespace}"
  }

  depends_on = [
    resource.null_resource.remove_strimzi
  ]
}

resource "kubernetes_manifest" "kafka_cluster" {
  count = var.enabled ? 1 : 0

  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind = "KafkaNodePool"
    metadata = {
      name = "dual-role"
      namespace = var.namespace
      labels = {
        "strimzi.io/cluster" = "trade-bots-farm"
      }
    }
    spec = {
      replicas = 1
      roles = ["controller", "broker"]
      storage = {
        type = "jbod"
        volumes = [{
          id = 0
          type = "persistent-claim"
          size = "10Gi"
          deleteClaim = true
          kraftMetadata = "shared"
        }]
      }
      template = {
        pod = {
          securityContext = {
            fsGroup = 1001
            runAsUser = 1001
          }
        }
      }
    }
  }

  depends_on = [
    resource.null_resource.install_strimzi
  ]
}

resource "kubernetes_manifest" "kafka_cluster_config" {
  count = var.enabled ? 1 : 0

  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind = "Kafka"
    metadata = {
      name = "trade-bots-farm"
      namespace = var.namespace
      annotations = {
        "strimzi.io/node-pools" = "enabled"
        "strimzi.io/kraft" = "enabled"
      }
    }
    spec = {
      kafka = {
        version = "4.0.0"
        metadataVersion = "4.0-IV3"
        listeners = [
          {
            name = "plain"
            port = 9092
            type = "internal"
            tls = false
          },
          {
            name = "tls"
            port = 9093
            type = "internal"
            tls = true
          },
          {
            name = "external"
            port = 9094
            type = "nodeport"
            tls = false
            configuration = {
              bootstrap = {
                nodePort = 31094
              }
            }
          }
        ]
        config = {
          "offsets.topic.replication.factor" = 1
          "transaction.state.log.replication.factor" = 1
          "transaction.state.log.min.isr" = 1
          "default.replication.factor" = 1
          "min.insync.replicas" = 1
        }
      }
    }
  }

  depends_on = [
    resource.null_resource.install_strimzi
  ]
}
