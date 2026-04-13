#!/bin/bash

# Environment and common libraries
set -a
source .env
source common-lib.sh
init_env
set +a
echo "Project root: $PROJECT_ROOT"

#AIRFLOW_WEBSERVER=$(kubectl get pods | grep airflow-webserver | awk '{print $1}')
AIRFLOW_WEBSERVER=$(kubectl get pods | grep airflow-api-server | awk '{print $1}')
AIRFLOW_DAGS_DIR=/opt/airflow/dags
AIRFLOW_ENV_DIR="/opt/trade-bots-farm/environment"
AIRFLOW_WHEELS_DIR="/opt/trade-bots-farm/wheels"
echo "Airflow webserver: $AIRFLOW_WEBSERVER"

copy_common_tools(){
  # Copy common module tool
    common_tools_file="$PROJECT_ROOT/common/src/common_tools.py"

    echo "Copying $common_tools_file to $AIRFLOW_WEBSERVER:$AIRFLOW_DAGS_DIR"
    kubectl cp "$common_tools_file" "$AIRFLOW_WEBSERVER":"$AIRFLOW_DAGS_DIR"

    dag_tools_file="$PROJECT_ROOT/common/src/dag_tools.py"

    echo "Copying dag_tools_file to $AIRFLOW_WEBSERVER:$AIRFLOW_DAGS_DIR"
    kubectl cp "$dag_tools_file" "$AIRFLOW_WEBSERVER":"$AIRFLOW_DAGS_DIR"

}

copy_dags() {
  module_dir=$1
  if [ -z "$module_dir" ]; then
      echo "Error: module_dir is parameter is required"
      return 1
  fi
  module_name=$2
  if [ -z "$module_name" ]; then
      echo "Error: module_name is parameter is required"
      return 1
  fi

  copy_common_tools

  # Find modules files in module, copy them to airflow
  for dag_src in "$module_dir"/src/*_dag.py
  do
    # Copy the module
    echo "Copying $dag_src to $AIRFLOW_WEBSERVER:$AIRFLOW_DAGS_DIR"
    kubectl cp "$dag_src" "$AIRFLOW_WEBSERVER":$AIRFLOW_DAGS_DIR

    # Copy .env file
    src_env_file="$module_dir/.env"
    dst_env_file="$AIRFLOW_ENV_DIR/$module_name.env"
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
  module_name=$2
  if [ -z "$module_dir" ]; then
      echo "Error: module_dir is parameter is required"
      return 1
  fi
  if [ -z "$module_name" ]; then
      echo "Error: module_name is parameter is required"
      return 1
  fi

  # Copy modules from module to airflow
  copy_dags "$module_dir" "$module_name"

  # Build module itself and copy it to airflow
  build_copy_module "$module_dir"


}

deploy_s3_sinks(){
  s3_sinks_dir=$1
  echo "Deploy s3 sinks from $s3_sinks_dir"
  for s3_sink_yaml in $s3_sinks_dir/*.yaml
  do
    echo "Deploy s3 sink $s3_sink_yaml"
    kubectl apply -f "$s3_sink_yaml"
  done
}

###############
# main
###############

set -e # Exit on error

modules=$*
echo "Dags to redeploy: $modules"

matched=false

for module in $modules
do
  echo "Processing module=$module"
  if [[ "$module" == "pytrade2" || "$module" == "all" ]]; then
      matched=true
      echo "Deploy pytrade2"
      build_copy_module "$PROJECT_ROOT/libs/pytrade2"
  fi
  if [[ "$module" == "common" || "$module" == "all" ]]; then
      matched=true
      echo "Deploy common module tools"
      build_copy_module "$PROJECT_ROOT/common"
      copy_common_tools
  fi
  if [[ "$module" == "connector_stream_alor" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/connectors/stream/alor-ws
        module_name="connector_stream_alor"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "connector_stream_htx" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/connectors/stream/htx-ws
        module_name="connector_stream_htx"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "connector_batch_s3_external" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/connectors/batch/s3-external
        module_name="connector_batch_s3_external"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "process_stream_staging_htx" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/stream/staging/htx
        module_name="process_stream_staging_htx"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "process_stream_staging_alor" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/stream/staging/alor
        module_name="process_stream_staging_alor"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "process_stream_features" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/stream/features
        module_name="process_stream_features_multi_indi"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "process_batch_staging_alor" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/batch/staging/alor
        module_name="process_batch_staging_alor"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "process_batch_staging_s3_external" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/batch/staging/s3-external
        module_name="processes_batch_staging_s3_external"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "process_batch_full" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/batch/full
        module_name="process_batch_full"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "process_stream_full" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/stream/full
        module_name="stream_full"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "process_common" || "$module" == "all" ]]; then
        matched=true
        module_dir=$PROJECT_ROOT/processes/common
        module_name="process_common"
        deploy_module "$module_dir" "$module_name"
  fi
  if [[ "$module" == "s3_sinks" || "$module" == "all" ]]; then
        matched=true
        deploy_s3_sink "$PROJECT_ROOT/connectors/stream/alor-ws/s3-sinks"
  fi

done


if [[ "$matched" == false ]]; then
    echo "ALERT: No matching condition found for module=$module"
    exit 1  # Optional: exit with error code
fi


