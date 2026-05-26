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

  # Force re-execution when the command content changes
  triggers = {
    command_sha256 = sha256(<<-EOT
set -e
echo '🚀 Installing/updating Strimzi operator...'
kubectl apply -f https://strimzi.io/install/latest?namespace=${var.namespace} -n ${var.namespace}
echo '⏳ Waiting for Strimzi CRDs to be established...'
kubectl wait --for=condition=Established crd -l app=strimzi --timeout=120s
echo '⏳ Waiting for kafka.strimzi.io API to be available...'
for i in $(seq 1 30); do
  if kubectl api-resources --api-group=kafka.strimzi.io 2>/dev/null | grep -q Kafka; then
    echo '✅ kafka.strimzi.io API resources available!'
    break
  fi
  echo "  attempt $i/30 - API not ready yet, waiting 2s..."
  sleep 2
done
kubectl api-resources --api-group=kafka.strimzi.io
echo '✅ Strimzi installation complete!'
EOT
    )
  }

  provisioner "local-exec" {
    command = <<EOT
set -e
echo '🚀 Installing/updating Strimzi operator...'
kubectl apply -f https://strimzi.io/install/latest?namespace=${var.namespace} -n ${var.namespace}
echo '⏳ Waiting for Strimzi CRDs to be established...'
kubectl wait --for=condition=Established crd -l app=strimzi --timeout=120s
echo '⏳ Waiting for kafka.strimzi.io API to be available...'
for i in $(seq 1 30); do
  if kubectl api-resources --api-group=kafka.strimzi.io 2>/dev/null | grep -q Kafka; then
    echo '✅ kafka.strimzi.io API resources available!'
    break
  fi
  echo "  attempt $i/30 - API not ready yet, waiting 2s..."
  sleep 2
done
kubectl api-resources --api-group=kafka.strimzi.io
echo '✅ Strimzi installation complete!'
EOT
  }

  depends_on = [
    resource.null_resource.remove_strimzi
  ]
}

resource "null_resource" "kafka_cluster" {
  count = var.enabled ? 1 : 0

  triggers = {
    manifest = sha256(<<-EOT
apiVersion: kafka.strimzi.io/v1
kind: KafkaNodePool
metadata:
  name: dual-role
  namespace: ${var.namespace}
  labels:
    strimzi.io/cluster: trade-bots-farm
spec:
  replicas: 1
  roles:
    - controller
    - broker
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 10Gi
        deleteClaim: true
        kraftMetadata: shared
  template:
    pod:
      securityContext:
        fsGroup: 1001
        runAsUser: 1001
EOT
    )
  }

  provisioner "local-exec" {
    command = <<EOT
set -e
echo '⏳ Applying KafkaNodePool...'
for i in $(seq 1 10); do
  if echo "
apiVersion: kafka.strimzi.io/v1
kind: KafkaNodePool
metadata:
  name: dual-role
  namespace: ${var.namespace}
  labels:
    strimzi.io/cluster: trade-bots-farm
spec:
  replicas: 1
  roles:
    - controller
    - broker
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 10Gi
        deleteClaim: true
        kraftMetadata: shared
  template:
    pod:
      securityContext:
        fsGroup: 1001
        runAsUser: 1001
" | kubectl apply -f - 2>/dev/null; then
    echo '✅ KafkaNodePool applied!'
    exit 0
  fi
  echo "  attempt $i/10 - API not ready yet, waiting 5s..."
  sleep 5
done
echo '❌ Failed to apply KafkaNodePool after 10 attempts'
exit 1
EOT
  }

  depends_on = [
    resource.null_resource.install_strimzi
  ]
}

resource "null_resource" "kafka_cluster_config" {
  count = var.enabled ? 1 : 0

  triggers = {
    manifest = sha256(<<-EOT
apiVersion: kafka.strimzi.io/v1
kind: Kafka
metadata:
  name: trade-bots-farm
  namespace: ${var.namespace}
  annotations:
    strimzi.io/node-pools: enabled
    strimzi.io/kraft: enabled
spec:
  kafka:
    version: 4.0.0
    metadataVersion: 4.0-IV3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
      - name: external
        port: 9094
        type: nodeport
        tls: false
        configuration:
          bootstrap:
            nodePort: 31094
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
      default.replication.factor: 1
      min.insync.replicas: 1
EOT
    )
  }

  provisioner "local-exec" {
    command = <<EOT
set -e
echo '⏳ Applying Kafka cluster config...'
for i in $(seq 1 10); do
  if echo "
apiVersion: kafka.strimzi.io/v1
kind: Kafka
metadata:
  name: trade-bots-farm
  namespace: ${var.namespace}
  annotations:
    strimzi.io/node-pools: enabled
    strimzi.io/kraft: enabled
spec:
  kafka:
    version: 4.0.0
    metadataVersion: 4.0-IV3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
      - name: external
        port: 9094
        type: nodeport
        tls: false
        configuration:
          bootstrap:
            nodePort: 31094
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
      default.replication.factor: 1
      min.insync.replicas: 1
" | kubectl apply -f - 2>/dev/null; then
    echo '✅ Kafka cluster config applied!'
    exit 0
  fi
  echo "  attempt $i/10 - API not ready yet, waiting 5s..."
  sleep 5
done
echo '❌ Failed to apply Kafka cluster config after 10 attempts'
exit 1
EOT
  }

  depends_on = [
    resource.null_resource.install_strimzi,
    resource.null_resource.kafka_cluster
  ]
}
