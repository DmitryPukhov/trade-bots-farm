#!/bin/bash
set -e

NAMESPACE=trade-bots-farm
echo "Namespace: $NAMESPACE"

PROJECT_ROOT=../../
echo "Project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT" || exit

SIDECAR_POD=$(kubectl get pods -n trade-bots-farm | grep scheduler | awk '{print $1}')
echo "Sidecar pod: $SIDECAR_POD"
POD_DAGS_DIR="/opt/airflow/dags"
POD_WHEELS_DIR="/opt/trade-bots-farm/wheels"
DIST_DIR="dist"
CONNECTOR_DIR="connectors/stream/htx-ws"
ENV_FILE_NAME="connector_stream_htx.env"

echo "Building wheels..."
uv build --package trade-bots-farm-common --wheel --out-dir $DIST_DIR
uv build --package trade-bots-farm-connector-stream-htx --wheel --out-dir $DIST_DIR

echo "Copying wheels to PVC..."
kubectl -n $NAMESPACE exec $SIDECAR_POD -- mkdir -p $POD_WHEELS_DIR
for whl in $DIST_DIR/trade_bots_farm_common-*.whl $DIST_DIR/trade_bots_farm_connector_stream_htx-*.whl; do
    kubectl -n $NAMESPACE cp "$whl" "$NAMESPACE/$SIDECAR_POD:$POD_WHEELS_DIR/"
done

echo "Copying dag_tools.py to DAGs dir..."
kubectl -n $NAMESPACE cp common/src/trade_bots_farm_common/dag_tools.py "$NAMESPACE/$SIDECAR_POD:$POD_DAGS_DIR/"

echo "Copying dag to DAGs dir..."
kubectl -n $NAMESPACE cp "$CONNECTOR_DIR/src/"*/*_dag.py "$NAMESPACE/$SIDECAR_POD:$POD_DAGS_DIR/"

echo "Copying .env to environment PVC..."
kubectl -n $NAMESPACE cp "$CONNECTOR_DIR/.env" "$NAMESPACE/$SIDECAR_POD:/opt/trade-bots-farm/environment/$ENV_FILE_NAME"

echo "Setting ownership and permissions..."
kubectl -n $NAMESPACE exec $SIDECAR_POD -- sh -c "chown -R airflow: $POD_DAGS_DIR/*.py"
kubectl -n $NAMESPACE exec $SIDECAR_POD -- sh -c "chmod +x $POD_DAGS_DIR/*.py"

echo "Verifying deployment..."
kubectl -n $NAMESPACE exec $SIDECAR_POD -- ls -la /opt/airflow/dags
kubectl -n $NAMESPACE exec $SIDECAR_POD -- ls -la $POD_WHEELS_DIR

echo "Deployed successfully"