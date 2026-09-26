#!/bin/bash
set -e

NAMESPACE=trade-bots-farm
CONNECTOR_NAME=htx-s3-sink
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KAFKA_CONNECT_DIR="$SCRIPT_DIR/../kafka-connect-s3"

echo "Namespace: $NAMESPACE"
echo "Connector: $CONNECTOR_NAME"


echo "Deploying KafkaConnector..."
kubectl apply -n "$NAMESPACE" -f "$KAFKA_CONNECT_DIR/htx-s3-sink.yaml"

echo "Verifying connector..."
sleep 5
kubectl get kafkaconnector htx-s3-sink -n "$NAMESPACE"

echo "Deployed successfully"