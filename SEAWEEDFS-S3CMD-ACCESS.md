# Accessing SeaweedFS with s3cmd

This guide explains how to access your SeaweedFS S3-compatible storage running in Minikube using `s3cmd` from your host machine.

## Prerequisites

1. **s3cmd installed** on your host machine:
   ```bash
   # Install s3cmd if not already installed
   sudo apt-get install s3cmd  # Debian/Ubuntu
   # or
   brew install s3cmd          # macOS
   ```

2. **Minikube running** with SeaweedFS deployed:
   ```bash
   minikube status
   ```

3. **SeaweedFS pods running**:
   ```bash
   kubectl get pods -n trade-bots-farm | grep seaweedfs
   ```

## Connection Details

Based on your Terraform configuration:

| Parameter | Value |
|-----------|-------|
| **S3 Endpoint** | `http://s3.tradebotsfarm.svc.cluster.local:8333` |
| **Access Key** | `minioadmin` |
| **Secret Key** | `minioadmin` |
| **Default Bucket** | `trade-bots-farm` |
| **Minikube IP** | `192.168.49.2` |
| **Namespace** | `trade-bots-farm` |

## DNS Resolution Solutions

Since SeaweedFS is accessed via ingress hostnames that require DNS resolution, you have several options:

### Option 1: Use Minikube Tunnel (Recommended for s3cmd)

Run minikube tunnel in a separate terminal:
```bash
minikube tunnel
# Keep this running in the background
```

This creates a network route that allows your host to resolve the `.svc.cluster.local` hostnames.

### Option 2: Configure System DNS

Configure your system to use Minikube's DNS server:
```bash
# Create systemd-resolved configuration
sudo tee /etc/systemd/resolved.conf.d/minikube.conf << 'EOF'
[Resolve]
DNS=192.168.49.2
Domains=~svc.cluster.local
EOF

# Restart systemd-resolved
sudo systemctl restart systemd-resolved
sudo resolvectl flush-caches
```

### Option 3: Use IP Address with Host Header (for testing)

For curl/testing, you can use the Minikube IP with a Host header:
```bash
curl -H "Host: s3.tradebotsfarm.svc.cluster.local" http://192.168.49.2/
```

## Configuring s3cmd

### Method 1: Interactive Configuration

Run the interactive configuration wizard:
```bash
s3cmd --configure
```

When prompted, enter:
- **Access Key**: `minioadmin`
- **Secret Key**: `minioadmin`
- **Default Region**: (leave empty or use `us-east-1`)
- **S3 Endpoint**: `http://s3.tradebotsfarm.svc.cluster.local:8333`
- **DNS-style bucket+hostname**: `%(bucket)s.s3.tradebotsfarm.svc.cluster.local`
- **Use HTTPS**: `No` (SeaweedFS uses HTTP)
- **Test access**: `Yes`
- **Save settings**: `Yes`

### Method 2: Manual Configuration File

Create or edit `~/.s3cfg`:
```ini
[default]
access_key = minioadmin
secret_key = minioadmin
host_base = s3.tradebotsfarm.svc.cluster.local:8333
host_bucket = %(bucket)s.s3.tradebotsfarm.svc.cluster.local
use_https = False
signature_v2 = True
check_ssl_certificate = False
check_ssl_hostname = False
```

**Important**: SeaweedFS uses signature v2, so you need `signature_v2 = True`.

### Method 3: Command-line Configuration

Create configuration with a single command:
```bash
cat > ~/.s3cfg << 'EOF'
[default]
access_key = minioadmin
secret_key = minioadmin
host_base = s3.tradebotsfarm.svc.cluster.local:8333
host_bucket = %(bucket)s.s3.tradebotsfarm.svc.cluster.local
use_https = False
signature_v2 = True
check_ssl_certificate = False
check_ssl_hostname = False
EOF
```

## Testing the Connection

### Test 1: List buckets
```bash
s3cmd ls
```

Expected output (showing the default bucket):
```
2026-04-25 10:30  s3://trade-bots-farm
```

### Test 2: List contents of default bucket
```bash
s3cmd ls s3://trade-bots-farm/
```

### Test 3: Create a test file and upload
```bash
echo "Hello SeaweedFS" > test.txt
s3cmd put test.txt s3://trade-bots-farm/
s3cmd ls s3://trade-bots-farm/
s3cmd get s3://trade-bots-farm/test.txt downloaded.txt
cat downloaded.txt
```

## Alternative Access Methods

### Using Port-Forward (No DNS Required)

If DNS resolution is problematic, you can use port-forwarding:

1. Forward the S3 service port:
   ```bash
   kubectl port-forward -n trade-bots-farm svc/seaweedfs-s3 8333:8333 &
   ```

2. Configure s3cmd to use localhost:
   ```ini
   host_base = localhost:8333
   host_bucket = %(bucket)s.localhost:8333
   ```

3. Test:
   ```bash
   s3cmd ls
   ```

### Using Minikube Service URL

Get the direct service URL:
```bash
minikube service -n trade-bots-farm seaweedfs-s3 --url
```

Use the returned URL in your s3cmd configuration.

## Common Issues and Solutions

### Issue 1: "SSL certificate problem"
**Solution**: Disable SSL certificate checking in `~/.s3cfg`:
```ini
check_ssl_certificate = False
check_ssl_hostname = False
```

### Issue 2: "SignatureDoesNotMatch" or "InvalidAccessKeyId"
**Solution**: Ensure you're using signature v2:
```ini
signature_v2 = True
```

### Issue 3: "Could not connect to endpoint"
**Solution**: Verify DNS resolution and that minikube tunnel is running:
```bash
# Test DNS resolution
nslookup s3.tradebotsfarm.svc.cluster.local

# Test connectivity
curl -H "Host: s3.tradebotsfarm.svc.cluster.local" http://192.168.49.2/
```

### Issue 4: "403 Forbidden"
**Solution**: Verify credentials match the Kubernetes secret:
```bash
kubectl get secret -n trade-bots-farm seaweedfs-s3-credentials -o jsonpath='{.data}' | base64 -d
```

## Advanced s3cmd Usage

### Sync a directory
```bash
s3cmd sync ./local-folder/ s3://trade-bots-farm/remote-folder/
```

### Set bucket policy
```bash
s3cmd setpolicy bucket-policy.json s3://trade-bots-farm
```

### Enable bucket versioning
```bash
s3cmd enable-versioning s3://trade-bots-farm
```

### Get bucket info
```bash
s3cmd info s3://trade-bots-farm
```

## Integration with Your Project

Your project already has S3 tools in `common/src/s3_tools.py`. You can use the same credentials:

```python
from common.src.s3_tools import S3Client

# The S3 client should be configured with the same endpoint
client = S3Client(
    endpoint_url="http://s3.tradebotsfarm.svc.cluster.local:8333",
    access_key="minioadmin",
    secret_key="minioadmin"
)
```

## Verification Script

Run this script to verify everything is working:

```bash
#!/bin/bash
set -e

echo "=== SeaweedFS s3cmd Verification ==="
echo ""

echo "1. Testing DNS resolution..."
if nslookup s3.tradebotsfarm.svc.cluster.local 192.168.49.2 >/dev/null 2>&1; then
    echo "   ✓ DNS resolution OK"
else
    echo "   ✗ DNS resolution failed"
    echo "   Starting minikube tunnel..."
    minikube tunnel >/dev/null 2>&1 &
    TUNNEL_PID=$!
    sleep 5
fi

echo ""
echo "2. Testing s3cmd configuration..."
if s3cmd ls >/dev/null 2>&1; then
    echo "   ✓ s3cmd connection successful"
    echo ""
    echo "3. Listing buckets:"
    s3cmd ls
else
    echo "   ✗ s3cmd connection failed"
    echo "   Check your ~/.s3cfg configuration"
fi

echo ""
echo "=== Verification complete ==="
```

## Troubleshooting

### Check SeaweedFS S3 service logs:
```bash
kubectl logs -n trade-bots-farm -l app.kubernetes.io/component=s3
```

### Check ingress controller logs:
```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=50
```

### Verify ingress configuration:
```bash
kubectl describe ingress -n trade-bots-farm seaweedfs-s3
```

## Conclusion

You now have multiple methods to access SeaweedFS using s3cmd. The recommended approach is:

1. Start `minikube tunnel` in a background terminal
2. Configure s3cmd with the endpoint `http://s3.tradebotsfarm.svc.cluster.local:8333`
3. Use signature v2 and disable SSL checks

This setup allows you to use SeaweedFS as an S3-compatible storage backend for your trade bots farm project.
