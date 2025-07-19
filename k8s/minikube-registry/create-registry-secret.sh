#!/bin/bash

# Generate TLS certs
MINIKUBE_IP=$(minikube ip)
openssl req -x509 -newkey rsa:4096 -nodes -days 365 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=registry.kube-system.svc.cluster.local" \
  -addext "subjectAltName=DNS:registry.kube-system.svc.cluster.local,DNS:registry,IP:${MINIKUBE_IP}"

# create secret in kube-system namespace
kubectl create secret tls registry-tls -n kube-system \
  --cert=tls.crt --key=tls.key