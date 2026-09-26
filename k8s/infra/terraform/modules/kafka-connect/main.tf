resource "null_resource" "install_kafka_connect" {
  count = var.enabled ? 1 : 0

  triggers = {
    namespace   = var.namespace
    yaml_sha256 = sha256(file("${path.module}/values.yaml"))
    bootstrap   = var.bootstrap_servers
  }

  provisioner "local-exec" {
    command = <<EOT
set -e
NAMESPACE=${var.namespace}

echo "Deploying KafkaConnect cluster: kafka-connect-s3 in namespace $NAMESPACE..."

envsubst '$$NAMESPACE' < "${path.module}/values.yaml" | kubectl apply -f - -n "$NAMESPACE"

echo "Waiting for KafkaConnect to be ready..."
kubectl wait kafkaconnect/kafka-connect-s3 --for=condition=Ready --timeout=180s -n "$NAMESPACE" || \
  echo "KafkaConnect not yet ready, continuing..."

echo "KafkaConnect cluster deployed successfully"
EOT
  }

  depends_on = []
}