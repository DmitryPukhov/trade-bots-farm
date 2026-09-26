# SeaweedFS Terraform Module

This module deploys SeaweedFS, a distributed object storage system, on Kubernetes using Helm and Terraform.

## Overview

SeaweedFS is a fast distributed storage system for blobs, objects, files, and data lake, with O(1) disk seeks in both reading and writing.

### Key Components

- **Master**: Manages the cluster and file system metadata
- **Volume Servers**: Store the actual data
- **Filer**: Provides file system interface for accessing data
- **S3 API**: S3-compatible API for object storage operations

## Usage

### Basic Usage

```hcl
module "seaweedfs" {
  source    = "./modules/seaweedfs"
  namespace = kubernetes_namespace.example.metadata[0].name
  enabled   = true
}
```

### With Custom Configuration

```hcl
module "seaweedfs" {
  source              = "./modules/seaweedfs"
  namespace           = "production"
  enabled             = true
  master_replicas     = 3
  volume_replicas     = 5
  s3_port             = 8333
  volume_size         = "50Gi"
  storage_class       = "fast-ssd"
  s3_access_key       = var.seaweedfs_access_key
  s3_secret_key       = var.seaweedfs_secret_key
  create_default_bucket = true
  default_bucket_name = "my-bucket"
}
```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `namespace` | Kubernetes namespace for SeaweedFS deployment | `string` | `"default"` | no |
| `enabled` | Whether to enable SeaweedFS deployment | `bool` | `true` | no |
| `master_replicas` | Number of SeaweedFS master replicas | `number` | `1` | no |
| `volume_replicas` | Number of SeaweedFS volume server replicas | `number` | `1` | no |
| `s3_port` | Port for SeaweedFS S3 API | `number` | `8333` | no |
| `volume_size` | Storage size for volume servers | `string` | `"10Gi"` | no |
| `storage_class` | Kubernetes storage class for persistent volumes | `string` | `"standard"` | no |
| `s3_access_key` | S3 access key for SeaweedFS | `string` | `"minioadmin"` | no |
| `s3_secret_key` | S3 secret key for SeaweedFS | `string` | `"minioadmin"` | no |
| `create_default_bucket` | Whether to create a default bucket | `bool` | `true` | no |
| `default_bucket_name` | Name of the default bucket to create | `string` | `"trade-bots-farm"` | no |
| `webui_auth_enabled` | Whether to enable basic authentication for web UI ingresses (master, filer, volume) | `bool` | `false` | no |
| `webui_auth_username` | Username for basic authentication | `string` | `"admin"` | no |
| `webui_auth_password` | Password for basic authentication | `string` | `""` | no |
| `webui_auth_secret_name` | Name of an existing Kubernetes secret containing basic auth credentials (key 'auth' with htpasswd format). If provided, the module will use this secret instead of creating a new one. | `string` | `""` | no |
| `webui_auth_secret_namespace` | Namespace of the existing basic auth secret. Defaults to var.namespace. | `string` | `""` | no |
| `create_webui_auth_secret` | Whether to create a Kubernetes secret for basic auth credentials. If false, you must provide an existing secret via webui_auth_secret_name. | `bool` | `false` | no |

## Web UI Authentication

To protect the SeaweedFS web UIs (master, filer, volume, and S3) with basic authentication, set `webui_auth_enabled = true`. The module will add nginx-ingress annotations to require authentication.

### Prerequisites

- NGINX Ingress Controller with basic auth support (the annotation `nginx.ingress.kubernetes.io/auth-type` must be recognized).
- A Kubernetes secret containing htpasswd formatted credentials in the key `auth`.

### Using an existing secret

If you already have a secret with htpasswd credentials, provide its name via `webui_auth_secret_name` and optionally `webui_auth_secret_namespace` (defaults to the same namespace). The secret must be of type `Opaque` with a key `auth` containing the htpasswd file content (e.g., `admin:$apr1$...`).

Example secret creation using `htpasswd`:

```bash
htpasswd -c auth admin
kubectl create secret generic seaweedfs-webui-auth --namespace <namespace> --from-file=auth
```

### Let the module create a secret

Set `create_webui_auth_secret = true` and provide `webui_auth_username` and `webui_auth_password`. The module will create a secret named `seaweedfs-webui-auth` (or the name you specify) using the provided credentials.

**Note:** The secret creation requires the `htpasswd` command to be available in the Terraform execution environment. If not available, you must create the secret manually.

### Example usage

```hcl
module "seaweedfs" {
  source = "./modules/seaweedfs"
  # ... other variables
  webui_auth_enabled           = true
  webui_auth_username          = "admin"
  webui_auth_password          = "securepassword"
  create_webui_auth_secret     = true
}
```

### Disabling authentication

Set `webui_auth_enabled = false` (default) to disable authentication.

## Outputs

| Name | Description |
|------|-------------|
| `service_host` | SeaweedFS S3 API service host |
| `service_port` | SeaweedFS S3 API service port |
| `filer_host` | SeaweedFS Filer service host |
| `filer_port` | SeaweedFS Filer service port |
| `master_host` | SeaweedFS Master service host |
| `master_port` | SeaweedFS Master service port |
| `s3_endpoint` | SeaweedFS S3 API endpoint |
| `s3_endpoint_external` | SeaweedFS S3 API external endpoint |
| `access_key` | SeaweedFS S3 access key |
| `secret_key` | SeaweedFS S3 secret key |
| `default_bucket_name` | Default bucket name |
| `operator_namespace` | Kubernetes namespace where SeaweedFS is deployed |
| `cluster_name` | SeaweedFS cluster name |

## Accessing SeaweedFS

### Within the Cluster

```bash
# S3 API endpoint
http://seaweedfs-s3.<namespace>.svc.cluster.local:8333

# Filer endpoint
http://seaweedfs-filer.<namespace>.svc.cluster.local:8888

# Master endpoint
http://seaweedfs-master.<namespace>.svc.cluster.local:9333
```

### Default Credentials

- **Access Key**: `minioadmin` (or as configured)
- **Secret Key**: `minioadmin` (or as configured)

## Configuration Files

### values.yaml

The `values.yaml` file contains Helm chart configuration for:
- Master server replicas and resources
- Volume server replicas, resources, and storage
- Filer configuration
- S3 API configuration
- Image configuration
- Network policies and TLS settings

### main.tf

The main Terraform configuration that:
- Installs SeaweedFS via Helm
- Creates S3 credentials secret
- Waits for SeaweedFS to be ready
- Creates default bucket using a Kubernetes Job
- Sets up service account for bucket creation

## Scaling

To scale the deployment:

```hcl
module "seaweedfs" {
  source          = "./modules/seaweedfs"
  namespace       = "default"
  master_replicas = 3  # Increase from 1 to 3
  volume_replicas = 5  # Increase from 1 to 5
}
```

## Storage

By default, SeaweedFS uses the "standard" storage class. To use a different storage class:

```hcl
module "seaweedfs" {
  source         = "./modules/seaweedfs"
  namespace      = "default"
  storage_class  = "fast-ssd"
  volume_size    = "100Gi"
}
```

## Disabling

To disable SeaweedFS deployment:

```hcl
module "seaweedfs" {
  source    = "./modules/seaweedfs"
  namespace = "default"
  enabled   = false
}
```

## Dependencies

This module depends on:
- Kubernetes cluster with persistent volume support
- Helm provider v2.13+
- Kubernetes provider v2.27+
- Time provider v0.9+

## Notes

- The default bucket is created with a 60-second delay to ensure SeaweedFS services are ready
- All credentials are marked as sensitive in Terraform output
- SeaweedFS services are created with resource requests and limits for stability
