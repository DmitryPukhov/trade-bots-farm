#!/bin/bash

# Environment and common libraries
set -a
source .env
source common-lib.sh
ensure_namespace
set +a

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

 function redeploy_airflow(){
  echo "Deleting old airflow"
  set +e
  helm delete airflow
  kubectl delete pvc airflow-dags
  set -e

  echo "Deploying airflow"
  # pvcs
  kubectl apply -f pvc/airflow-dags.yaml
  kubectl apply -f pvc/environment.yaml
  kubectl apply -f pvc/wheels.yaml

  helm repo add apache-airflow https://airflow.apache.org
  helm upgrade --install airflow apache-airflow/airflow -f airflow/values.yaml
 }

function redeploy_kafka(){
  echo "Redeploying kafka"
  # Delete previous ignoring errors if not exist
  set +e
      kubectl -n $NAMESPACE delete $(kubectl get strimzi -o name -n $NAMESPACE)
      kubectl delete pvc -l strimzi.io/name=trade-bots-farm -n $NAMESPACE
      kubectl -n $NAMESPACE delete -f "https://strimzi.io/install/latest?namespace=$NAMESPACE"
  set -e

  # Install kafka operator
  kubectl create -f "https://strimzi.io/install/latest?namespace=$NAMESPACE" -n $NAMESPACE
  # Install kafka cluster
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

function redeploy_minikube_registry(){
  # Disable existing registry
  minikube addons disable registry

  # Create PV and PVC
  kubectl apply -f minikube-registry/registry-pv.yaml -n kube-system
  kubectl apply -f minikube-registry/registry-pvc.yaml -n kube-system

  # Configure registry to use registry-pvc
cat <<EOF | minikube addons configure registry -f -
persistence:
  enabled: true
  existingClaim: registry-pvc
  storageClass: manual
  accessMode: ReadWriteOnce
  size: 10Gi
EOF
  #minikube addons configure registry -f minikube-registry/registry-config.yaml

  # Enable registry
  minikube addons enable registry

}

###############
# main
###############
# Exit on error
set -e

#modules=${*:-"secrets prometheus mlflow grafana kafka kafka-ui airflow"}
modules=$*
echo "Modules to redeploy: $modules"
for module in $modules
do
  # Call redeploy_ function for one module
  $"redeploy_$module"
done

