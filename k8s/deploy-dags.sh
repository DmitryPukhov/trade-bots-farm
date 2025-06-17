#!/bin/bash

# Environment and common libraries
set -a
source .env
source common-lib.sh
init_env
set +a
echo "Project root: $PROJECT_ROOT"

AIRFLOW_WEBSERVER=$(kubectl get pods | grep airflow-webserver | awk '{print $1}')
AIRFLOW_DAGS_DIR=/opt/airflow/dags
AIRFLOW_ENV_DIR="/opt/trade-bots-farm/environment"
AIRFLOW_WHEELS_DIR="/opt/trade-bots-farm/wheels"
echo "Airflow webserver: $AIRFLOW_WEBSERVER"
copy_dag_tools(){
  # Copy common dag tool
    dag_tools_file="$PROJECT_ROOT/common/src/dag_tools.py"
    echo "Copying $dag_tools_file to $AIRFLOW_WEBSERVER:$AIRFLOW_DAGS_DIR"
    kubectl cp "$dag_tools_file" "$AIRFLOW_WEBSERVER":"$AIRFLOW_DAGS_DIR"

}

copy_dags() {
  module_dir=$1
  if [ -z "$module_dir" ]; then
      echo "Error: module_dir is parameter is required"
      return 1
  fi
  dag_name=$2
  if [ -z "$dag_name" ]; then
      echo "Error: dag_name is parameter is required"
      return 1
  fi

  copy_dag_tools

  # Find dags files in module, copy them to airflow
  for dag_src in "$module_dir"/src/*_dag.py
  do
    # Copy the dag
    echo "Copying $dag_src to $AIRFLOW_WEBSERVER:$AIRFLOW_DAGS_DIR"
    kubectl cp "$dag_src" "$AIRFLOW_WEBSERVER":$AIRFLOW_DAGS_DIR

    # Copy .env file
    src_env_file="$module_dir/.env"
    dst_env_file="$AIRFLOW_ENV_DIR/$dag_name.env"
    echo "Copying $src_env_file to $AIRFLOW_WEBSERVER:$dst_env_file"
    kubectl cp "$src_env_file" "$AIRFLOW_WEBSERVER":$dst_env_file
  done
  echo "Completed. Dags from $module_dir copied to $AIRFLOW_WEBSERVER:$AIRFLOW_DAGS_DIR."

}

build_copy_module() {
  module_dir=$1
  if [ -z "$module_dir" ]; then
      echo "Error: module_dir is parameter is required"
      return 1
  fi
  #  echo "Building module $module_dir"
  wheels_dir="$PROJECT_ROOT"/.wheels/
  cd "$module_dir"
  pip wheel . --wheel-dir="$wheels_dir" --find-links="$wheels_dir"
  cd "$OLD_PWD"
  echo "Module $module_dir built to $wheels_dir"

  echo "Copying $wheels_dir to airflow $AIRFLOW_WEBSERVER:$AIRFLOW_WHEELS_DIR"
  #kubectl cp "$wheels_dir" "$AIRFLOW_WEBSERVER":"$AIRFLOW_WHEELS_DIR"
  (cd "$PROJECT_ROOT"/.wheels && tar cf - *.whl) | kubectl exec -i $AIRFLOW_WEBSERVER -- tar xf - -C $AIRFLOW_WHEELS_DIR
  echo "Completed. Deployed $module_dir"
}

deploy_module() {
  module_dir=$1
  dag_name=$2
  if [ -z "$module_dir" ]; then
      echo "Error: module_dir is parameter is required"
      return 1
  fi
  if [ -z "$dag_name" ]; then
      echo "Error: dag_name is parameter is required"
      return 1
  fi

  # Copy dags from module to airflow
  copy_dags "$module_dir" "$dag_name"

  # Build module itself and copy it to airflow
  build_copy_module "$module_dir"
}


###############
# main
###############

set -e # Exit on error

dags=$*
echo "Dags to redeploy: $dags"

matched=false

for dag in $dags
do
  echo "Processing dag=$dag"
  if [[ "$dag" == "pytrade2" || "$dag" == "all" ]]; then
      matched=true
      echo "Deploy pytrade2"
      build_copy_module "$PROJECT_ROOT/libs/pytrade2"
  fi
  if [[ "$dag" == "common" || "$dag" == "all" ]]; then
      matched=true
      echo "Deploy common dag tools"
      build_copy_module "$PROJECT_ROOT/common"
      copy_dag_tools
  fi
  if [[ "$dag" == "connector_stream_htx" || "$dag" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/connectors/stream/htx-ws
        dag_name="connector_stream_htx"
        deploy_module "$module_dir" "$dag_name"
  fi
  if [[ "$dag" == "connector_batch_s3_external" || "$dag" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/connectors/batch/s3-external
        dag_name="connector_batch_s3_external"
        deploy_module "$module_dir" "$dag_name"
  fi
  if [[ "$dag" == "process_stream_raw_to_preproc" || "$dag" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/stream/raw-to-preproc
        dag_name="process_stream_raw_to_preproc"
        deploy_module "$module_dir" "$dag_name"
  fi
  if [[ "$dag" == "process_stream_features" || "$dag" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/stream/features
        dag_name="process_stream_features_multi_indi"
        deploy_module "$module_dir" "$dag_name"
  fi
  if [[ "$dag" == "process_batch_raw_to_preproc" || "$dag" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/batch/raw-to-preproc
        dag_name="process_batch_raw_to_preproc"
        deploy_module "$module_dir" "$dag_name"
  fi
  if [[ "$dag" == "process_batch_full" || "$dag" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/batch/full
        dag_name="process_batch_full"
        deploy_module "$module_dir" "$dag_name"
  fi
done


if [[ "$matched" == false ]]; then
    echo "ALERT: No matching condition found for dag=$dag"
    exit 1  # Optional: exit with error code
fi


