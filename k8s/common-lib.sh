

# Create namespace if does not exist
function ensure_namespace() {
  if kubectl get ns "$NAMESPACE" >/dev/null 2>&1; then
    echo "Namespace '$NAMESPACE' is found."
  else
    echo "Creating namespace '$NAMESPACE'..."
    kubectl create namespace "$NAMESPACE"
  fi
  kubectl config set-context --current --namespace="$NAMESPACE"
  echo "Namespace '$NAMESPACE' set default."
}
function set_project_root() {
  root_dir_name="trade-bots-farm"
  dir=$(pwd)
  while [[ "$dir" != "/" ]]; do
      if [[ "$(basename "$dir")" == "$root_dir_name" ]]; then
          PROJECT_ROOT=$dir
          export PROJECT_ROOT
          echo "Project root: $PROJECT_ROOT"
          return
      fi
      dir=$(dirname "$dir")
  done
  echo "Project root $root_dir_name not found."
  exit 1

}

function init_env() {
  ensure_namespace
  set_project_root
}