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
POD_APP_DIR=/opt/trade-bots-farm

# Ensure we're in the correct directory
if [ ! -d "connectors/stream/alor-ws" ]; then
    echo "❌ Directory connectors/stream/alor-ws not found"
    exit 1
fi

cd "connectors/stream/alor-ws" || exit

# Create virtual environment and install dependencies
#echo "📦 Creating virtual environment and installing dependencies..."
#uv venv .venv --seed
#uv pip install -e .

echo "📁 Copying .venv to PVC..."
kubectl -n $NAMESPACE cp ./.venv $NAMESPACE/$SIDECAR_POD:$POD_APP_DIR/.venv
#
#echo "📁 Copying src to PVC..."
#kubectl -n $NAMESPACE cp ./src $NAMESPACE/$SIDECAR_POD:$POD_DAGS_DIR/src

echo "📁 Copying dag to PVC..."
kubectl -n $NAMESPACE cp ./src/*/*_dag.py $NAMESPACE/$SIDECAR_POD:$POD_DAGS_DIR

echo "🔧 Changing owner to airflow:airflow"
kubectl -n $NAMESPACE exec $SIDECAR_POD -- chown -R airflow: $POD_DAGS_DIR/*.py
kubectl -n $NAMESPACE exec $SIDECAR_POD -- chmod +x $POD_DAGS_DIR/*.py

# Verify the copy was successful
echo "🔍 Verifying deployment..."
kubectl -n $NAMESPACE exec $SIDECAR_POD -- ls -la /opt/airflow/dags

cd $PROJECT_ROOT
echo "✅ Deployed successfully to airflow-dags PVC"

cd "$OLDPWD" 2>/dev/null || true
