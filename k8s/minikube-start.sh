#!/bin/bash
HOST_REGISTRY_PATH="$HOME/.minikube-registry"
MINIKUBE_REGISTRY_PATH="/var/lib/registry"
echo "Starting minikube"
echo "Mounting host $HOST_REGISTRY_PATH to minikube $MINIKUBE_REGISTRY_PATH"

minikube start --driver=kvm2 --cpus=4 --memory=16384  --mount --mount-string=$"$HOST_REGISTRY_PATH:$MINIKUBE_REGISTRY_PATH"
minikube addons enable metrics-server
minikube addons enable registry