#!/bin/bash
set -e

NAMESPACE=trade-bots-farm
echo "Namespace: $NAMESPACE"

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/../..")
echo "Project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT" || exit

SIDECAR_POD=$(kubectl get pods -n trade-bots-farm -l component=scheduler -o jsonpath="{.items[0].metadata.name}")
DAG_PROCESSOR_POD=$(kubectl get pods -n trade-bots-farm -l component=dag-processor -o jsonpath="{.items[0].metadata.name}")
API_SERVER_POD=$(kubectl get pods -n trade-bots-farm -l component=api-server -o jsonpath="{.items[0].metadata.name}")
echo "Scheduler pod: $SIDECAR_POD"
echo "API server pod: $API_SERVER_POD"
POD_DAGS_DIR="/opt/airflow/dags"
POD_WHEELS_DIR="/home/airflow/trade-bots-farm/wheels"
DIST_DIR="dist"
CONNECTOR_DIR="connectors/stream/alor-ws"
ENV_FILE_NAME="connector_stream_alor.env"

echo "Building wheels..."
uv build --package trade-bots-farm-common --wheel --out-dir $DIST_DIR
uv build --package trade-bots-farm-connector-stream-alor --wheel --out-dir $DIST_DIR

echo "Copying wheels to PVC..."
for pod in $SIDECAR_POD $API_SERVER_POD; do
    kubectl -n $NAMESPACE exec $pod -- mkdir -p $POD_WHEELS_DIR /home/airflow/trade-bots-farm/environment
    for whl in $DIST_DIR/trade_bots_farm_common-*.whl $DIST_DIR/trade_bots_farm_connector_stream_alor-*.whl; do
        kubectl -n $NAMESPACE cp "$whl" "$NAMESPACE/$pod:$POD_WHEELS_DIR/"
    done
done

echo "Copying dag_tools.py to DAGs dir..."
for pod in $SIDECAR_POD $API_SERVER_POD $DAG_PROCESSOR_POD; do
    kubectl -n $NAMESPACE cp common/src/trade_bots_farm_common/dag_tools.py "$NAMESPACE/$pod:$POD_DAGS_DIR/"
done

echo "Copying dag to DAGs dir..."
for dag_file in $CONNECTOR_DIR/src/*/*_dag.py; do
    for pod in $SIDECAR_POD $API_SERVER_POD $DAG_PROCESSOR_POD; do
        kubectl -n $NAMESPACE cp "$dag_file" "$NAMESPACE/$pod:$POD_DAGS_DIR/"
    done
done

echo "Copying .env to environment PVC..."
for pod in $SIDECAR_POD $API_SERVER_POD; do
    kubectl -n $NAMESPACE cp "$CONNECTOR_DIR/.env" "$NAMESPACE/$pod:/home/airflow/trade-bots-farm/environment/$ENV_FILE_NAME"
done

echo "Setting ownership and permissions..."
for pod in $SIDECAR_POD $API_SERVER_POD; do
    kubectl -n $NAMESPACE exec $pod -- sh -c "chown -R airflow: $POD_DAGS_DIR/*.py && chown -R airflow: /home/airflow/trade-bots-farm"
    kubectl -n $NAMESPACE exec $pod -- sh -c "chmod +x $POD_DAGS_DIR/*.py"
done

echo "Verifying deployment..."
kubectl -n $NAMESPACE exec $SIDECAR_POD -- ls -la /opt/airflow/dags
kubectl -n $NAMESPACE exec $SIDECAR_POD -- ls -la $POD_WHEELS_DIR

echo "Deployed successfully"