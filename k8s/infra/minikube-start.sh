#!/bin/bash


echo "Starting minikube"
echo "Mounting host $HOST_REGISTRY_PATH to minikube $MINIKUBE_REGISTRY_PATH"
HOST_DOCKER_CERTS_PATH=/etc/docker/certs.d
MINIKUBE_DOCKER_CERTS_PATH=/etc/docker/certs.d

minikube start --driver=kvm2 --cpus=6 --memory=32g  --mount --mount-string=$HOST_DOCKER_CERTS_PATH:$MINIKUBE_DOCKER_CERTS_PATH

# Configure Docker log rotation to prevent container log files from filling up disk
echo "Configuring Docker log rotation on minikube..."
minikube ssh -- sudo mkdir -p /etc/docker
minikube ssh -- sudo tee /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
minikube ssh -- sudo systemctl restart docker

# Configure logrotate for container logs
echo "Configuring logrotate for container logs..."
minikube ssh -- sudo tee /etc/logrotate.d/kube-containers << 'EOF'
/var/lib/docker/containers/*/*.log {
  rotate 7
  daily
  compress
  missingok
  delaycompress
  copytruncate
  maxsize 50M
}
EOF

echo "Docker log rotation configured successfully."
