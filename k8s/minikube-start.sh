#!/bin/bash


echo "Starting minikube"
echo "Mounting host $HOST_REGISTRY_PATH to minikube $MINIKUBE_REGISTRY_PATH"
HOST_DOCKER_CERTS_PATH=/etc/docker/certs.d
MINIKUBE_DOCKER_CERTS_PATH=/etc/docker/certs.d

minikube start --driver=kvm2 --cpus=6 --memory=32g  --mount --mount-string=$HOST_DOCKER_CERTS_PATH:$MINIKUBE_DOCKER_CERTS_PATH
#minikube addons enable metrics-server
