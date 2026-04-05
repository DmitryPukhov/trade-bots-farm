resource "kubernetes_pod" "kafka_connect_build" {
  metadata {
    name = "kafka-connect-build"
  }

  spec {
    container {
      name  = "docker"
      image = "docker:20.10-dind"

      command = ["/bin/sh", "-c"]
      args = [
        "docker build -t ${var.docker_registry}/kafka-connect-s3:latest -f /workspace/kafka-connect/Dockerfile . && \
         docker push ${var.docker_registry}/kafka-connect-s3:latest"
      ]

      volume_mount {
        name       = "docker-graph-storage"
        mount_path = "/var/lib/docker"
      }

      volume_mount {
        name       = "workspace"
        mount_path = "/workspace"
      }

      security_context {
        privileged = true
      }
    }

    volume {
      name = "docker-graph-storage"
      empty_dir {}
    }

    volume {
      name = "workspace"
      host_path {
        path = "${path.root}/../../.."
      }
    }
  }

  provisioner "local-exec" {
    command = "echo 'Waiting for Docker daemon to start...'; sleep 10"
  }
}

resource "kubernetes_manifest" "kafka_connect" {
  manifest = yamldecode(file("../../kafka-connect/kafka-connect-s3.yaml"))

  depends_on = [
    resource.kubernetes_pod.kafka_connect_build
  ]
}

resource "kubernetes_manifest" "kafka_connectors" {
  manifest = yamldecode(file("../../kafka-connect/alor-s3-sink.yaml"))

  depends_on = [
    resource.kubernetes_manifest.kafka_connect
  ]
}