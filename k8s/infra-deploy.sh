#!/bin/bash

# Environment and common libraries
set -a
source .env
source common-lib.sh
ensure_namespace
set +a

DOCKER_REGISTRY=$(minikube ip):30500

# All secrets
function redeploy_secrets(){
  for yaml_file in secret/*.yaml; do
      set +e
      echo "Trying to delete old secret $yaml_file"
      secret_name=$(basename "${yaml_file%.*}")
      kubectl delete secret "$secret_name"
      set -e
      # Deploy the secret
      echo "Deploying secret $yaml_file"
      kubectl apply -f "$yaml_file"
  done
}

function redeploy_minio(){
  echo "Deleting old minio"
  set +e
  helm delete minio
  #kubectl delete pvc minio
  set -e
  echo "Deploying minio"
  #kubectl apply -f pvc/minio.yaml
  helm install minio oci://registry-1.docker.io/bitnamicharts/minio  --values minio/values.yaml
}

# Mlflow run, tracking, postgresql
function redeploy_mlflow(){
  echo "Redeploying mlflow"
  # Delete previous ignoring errors if not exists
  set +e
  helm delete mlflow
  kubectl delete pvc data-mlflow-postgresql-0
  kubectl delete pvc mlflow-tracking
  set -e

  # Install mlflow
  helm install mlflow oci://registry-1.docker.io/bitnamicharts/mlflow --values mlflow/values.yaml
}

function redeploy_prometheus(){
  echo "Redeploying prometheus"
  set +e
  helm delete prometheus
  helm delete prometheus-pushgateway
  #kubectl delete pvc prometheus-0
  set -e
  helm install prometheus oci://registry-1.docker.io/bitnamicharts/prometheus --values prometheus/values.yaml --set serviceMonitor.enabled=true
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm install prometheus-pushgateway prometheus-community/prometheus-pushgateway --values prometheus/prometheus-pushgateway.values.yaml
}

# Grafana
function redeploy_grafana(){
  echo "Redeploying grafana"
  # Delete previous ignoring errors if not exists
  set +e
  helm delete grafana
  kubectl delete pvc grafana
  set -e

  # install grafana
  helm install grafana oci://registry-1.docker.io/bitnamicharts/grafana --values grafana/values.yaml
}

function remove_airflow(){
  echo "Deleting old airflow"
  set +e
  helm delete --cascade=foreground airflow

  set -euo pipefail

  # Force delete Terminating PVCs
  echo "Deleting old PVCs"
  for pvc in $(kubectl get pvc --no-headers | grep -E 'airflow|environment|wheels' | awk '{print $1}');
  do
      echo "Force deleting PVC: $pvc"
      kubectl patch pvc "$pvc" -p '{"metadata":{"finalizers":null}}'
      kubectl delete --force pvc "$pvc"
  done

  # Wait a few seconds
  #sleep 5

  # Force delete Terminating PVs
  echo "Deleting old PVs"
  for pv in $(kubectl get pv --no-headers | grep -E 'airflow|environment|wheels' | awk '{print $1}');
  do
      echo "Force deleting PV: $pv"
      kubectl patch pv "$pv" -p '{"metadata":{"finalizers":null}}'
      kubectl delete --force pv "$pv"
  done

  echo "Deleting old statefulsets"
  for name in $(kubectl get statefulset | grep airflow | awk '{print $1}')
  do
    echo "Deleting statefulset $name"
    kubectl delete statefulset $name
  done

  set -e
  echo "Cleaned up"
}
 function redeploy_airflow(){
  echo "Deleting old airflow"
  set +e
  helm delete --cascade=foreground airflow
  set -e

  echo "Deploying airflow"
  # pvcs
  kubectl apply -f pvc/airflow-dags.yaml
  kubectl apply -f pvc/environment.yaml
  kubectl apply -f pvc/wheels.yaml

  helm repo add apache-airflow https://airflow.apache.org
  helm install airflow apache-airflow/airflow -f airflow/values.yaml --debug
 }

function remove_strimzi() {
    echo "🚀 Starting Strimzi/Kafka uninstall..."

    # Delete all Kafka custom resources
    kubectl delete $(kubectl get kafka,kafkatopics,kafkausers,kafkaconnects,kafkabridges,kafkamirrormaker2 -o name -n $NAMESPACE 2>/dev/null) --ignore-not-found

    # Delete Cluster Operator and other deployments
    kubectl delete deployment -l app=strimzi -n $NAMESPACE --ignore-not-found

    # Delete all Strimzi CRDs
    kubectl delete crd -l app=strimzi --ignore-not-found

    # Delete cluster-wide RBAC resources
    kubectl delete clusterrolebinding,clusterrole,clusterroles,rolebindings,configmaps -l app=strimzi --ignore-not-found

    # Delete webhook configurations
    kubectl delete validatingwebhookconfigurations,mutatingwebhookconfigurations -l app=strimzi --ignore-not-found

    # Delete service accounts
    kubectl delete serviceaccount -l app=strimzi -n $NAMESPACE --ignore-not-found

    # Delete persistent volumes (optional)
    kubectl delete pvc -n $NAMESPACE -l app.kubernetes.io/name=kafka --ignore-not-found
    kubectl delete pvc -n $NAMESPACE -l app.kubernetes.io/name=zookeeper --ignore-not-found

    # Remove finalizers from all Kafka resources
    kubectl get kafka -n $NAMESPACE -o name | xargs -I {} kubectl patch {} -n $NAMESPACE -p '{"metadata":{"finalizers":[]}}' --type=merge

    # Force delete CRDs
    kubectl get crd -l app=strimzi -o name | xargs -I {} kubectl patch {} -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "✅ Strimzi/Kafka uninstallation complete!"
}

function redeploy_kafka(){
  # Delete previous ignoring errors if not exist
  set +e
      echo "Try to delete old kafka from $NAMESPACE"
      remove_strimzi

  set -e
  echo "Deploying kafka"
#  # Install kafka operator
  kubectl create -v=6 -f "https://strimzi.io/install/latest?namespace=$NAMESPACE" -n $NAMESPACE
#  # Install kafka cluster
  kubectl apply -f kafka/values.yaml -n $NAMESPACE
 }

 function redeploy_kafka-ui(){
   echo "Redeploying kafka-ui"
   set +e
   helm delete kafka-ui
   set -e

   helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
   #helm repo update
   helm install kafka-ui kafka-ui/kafka-ui  -f kafka-ui/values.yaml
 }

 function redeploy_kafka-connectors(){
   set +e
   echo "Try to delete old kafka connectors"
   kubectl delete kafkaconnector alor-s3-sink
   set -e
   echo "Deploying kafka connectors"
   kubectl apply -f kafka-connect/alor-s3-sink.yaml
 }
 function redeploy_kafka-connect(){
    echo "Redeploying kafka-connect"

    echo "Build and push docker image"

    echo "Docker registry: $DOCKER_REGISTRY"
    docker build -t "$DOCKER_REGISTRY"/kafka-connect-s3:latest -f  kafka-connect/Dockerfile .
    docker push "$DOCKER_REGISTRY"/kafka-connect-s3:latest

     set +e
     echo "Try to delete old kafka connect "
     kubectl delete kafkaconnect kafka-connect-s3
     set -e

     echo "Deploy kafka connect"
     kubectl apply -f kafka-connect/kafka-connect-s3.yaml
 }

 function redeploy_registry(){
    kubectl apply -f minikube-registry/registry-pv.yaml
    kubectl apply -f minikube-registry/registry-pvc.yaml
    kubectl apply -f minikube-registry/registry-deployment.yaml

    echo "Copy docker image registry certs to minikube node"
    certs_dir="sudo mkdir -p /etc/docker/certs.d/$DOCKER_REGISTRY"
    minikube ssh "sudo mkdir -p $certs_dir"
    minikube cp secret/registry/tls.crt "$certs_dir"/ca.crt
 }

###############
# main
###############
# Exit on error
set -e

#modules=${*:-"secrets minio prometheus mlflow grafana kafka kafka-ui kafka-connect airflow"}
modules=$*
echo "Modules to redeploy: $modules"
for module in $modules
do
  # Call redeploy_ function for one module
  $"redeploy_$module"
done

