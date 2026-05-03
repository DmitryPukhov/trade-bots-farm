# SeaweedFS Ingress Access Solutions

## Problem Analysis
Your SeaweedFS Terraform deployment has correctly configured ingress resources, but you cannot access them from your host machine browser. The issue is DNS resolution, not the ingress configuration itself.

## Current Configuration
- **S3 Ingress Host**: `s3.tradebotsfarm.svc.cluster.local`
- **Filer Ingress Host**: `filer.tradebotsfarm.svc.cluster.local`
- **Master Ingress Host**: `master.tradebotsfarm.svc.cluster.local`
- **Minikube IP**: `192.168.49.2`
- **Ingress Controller**: nginx (running)
- **SeaweedFS Services**: All pods are running
- **Ingress Resources**: 3 separate ingresses with host-based routing (s3, filer, master)

## Root Cause
The hostnames `s3.tradebotsfarm.svc.cluster.local`, `filer.tradebotsfarm.svc.cluster.local`, and `master.tradebotsfarm.svc.cluster.local` resolve correctly via Minikube's DNS server (`192.168.49.2:53`) but not via your system's default DNS resolver.

## Solutions

### Solution 1: Configure System DNS (Recommended)
Configure your system to use Minikube's DNS server for `.svc.cluster.local` domains:

```bash
# Create systemd-resolved configuration
sudo tee /etc/systemd/resolved.conf.d/minikube.conf << 'EOF'
[Resolve]
DNS=192.168.49.2
Domains=~svc.cluster.local
EOF

# Restart systemd-resolved
sudo systemctl restart systemd-resolved

# Flush DNS cache
sudo resolvectl flush-caches
```

**Verification**:
```bash
nslookup seaweedfs.tradebotsfarm.svc.cluster.local
ping -c 2 seaweedfs.tradebotsfarm.svc.cluster.local
```

### Solution 2: Use Minikube Tunnel (Easiest)
Run minikube tunnel in a separate terminal:
```bash
minikube tunnel
# Keep this running in the background
```

Then access in your browser:
- S3 API: http://s3.tradebotsfarm.svc.cluster.local/
- Filer UI: http://filer.tradebotsfarm.svc.cluster.local/
- Master UI: http://master.tradebotsfarm.svc.cluster.local/

### Solution 3: Browser Workaround
Use a browser extension like "ModHeader" (Chrome/Firefox):

For S3 API:
1. Install ModHeader extension
2. Add a request header:
   - Name: `Host`
   - Value: `s3.tradebotsfarm.svc.cluster.local`
3. Access: http://192.168.49.2/

For Filer UI:
1. Change the Host header value to: `filer.tradebotsfarm.svc.cluster.local`
2. Access: http://192.168.49.2/

For Master UI:
1. Change the Host header value to: `master.tradebotsfarm.svc.cluster.local`
2. Access: http://192.168.49.2/

### Solution 4: Command Line Access
For testing or scripting, use curl with Host header:

```bash
# S3 API
curl -H "Host: s3.tradebotsfarm.svc.cluster.local" http://192.168.49.2/

# Filer UI
curl -H "Host: filer.tradebotsfarm.svc.cluster.local" http://192.168.49.2/

# Master UI
curl -H "Host: master.tradebotsfarm.svc.cluster.local" http://192.168.49.2/
```

**Note**: With the new host-based routing, each service is accessed at the root path `/` on its own subdomain.

### Solution 5: Update Terraform Configuration
The Terraform configuration now supports separate hostnames for each SeaweedFS service. To customize the hostnames:

1. Edit `k8s/terraform/terraform.tfvars`:
   ```hcl
   # Base hostname (used as fallback if specific hostnames are not set)
   seaweedfs_ingress_host = "seaweedfs.tradebotsfarm.svc.cluster.local"
    
   # Individual service hostnames (optional - if empty, uses the base hostname)
   seaweedfs_s3_ingress_host = "s3.tradebotsfarm.svc.cluster.local"
   seaweedfs_filer_ingress_host = "filer.tradebotsfarm.svc.cluster.local"
   seaweedfs_master_ingress_host = "master.tradebotsfarm.svc.cluster.local"
   ```

2. Apply changes:
   ```bash
   cd k8s/terraform
   terraform apply
   ```

## Quick Test Script
Run the diagnostic script to verify connectivity:
```bash
chmod +x k8s/terraform/fix-seaweedfs-dns.sh
./k8s/terraform/fix-seaweedfs-dns.sh
```

## Access URLs
Once DNS is resolved, access these URLs:

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| S3 API | http://s3.tradebotsfarm.svc.cluster.local/ | 8333 | S3-compatible API |
| Filer UI | http://filer.tradebotsfarm.svc.cluster.local/ | 8888 | Web file manager |
| Master UI | http://master.tradebotsfarm.svc.cluster.local/ | 9333 | Cluster management |

**Note**: The configuration now uses separate hostnames for each service instead of path-based routing. This allows accessing each service directly via its own subdomain.

## S3 Credentials (from Terraform)
- **Access Key**: `minioadmin` (default)
- **Secret Key**: `minioadmin` (default)
- **Bucket**: `trade-bots-farm` (default bucket)

## Verification Steps
1. Run diagnostics: `./k8s/terraform/fix-seaweedfs-dns.sh`
2. Check pods: `kubectl get pods -n trade-bots-farm | grep seaweedfs`
3. Check ingress: `kubectl get ingress -n trade-bots-farm`
4. Test connectivity with curl (see Solution 4)

## Troubleshooting
If still not working:

1. **Check minikube addons**:
   ```bash
   minikube addons list | grep ingress
   ```

2. **Restart ingress-dns**:
   ```bash
   minikube addons disable ingress-dns
   minikube addons enable ingress-dns
   ```

3. **Check ingress controller logs**:
   ```bash
   kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=20
   ```

4. **Verify ingress rules**:
   ```bash
   kubectl describe ingress -n trade-bots-farm
   ```

## Conclusion
The ingress configuration is correct. The issue is purely DNS resolution. Solution 1 (system DNS configuration) or Solution 2 (minikube tunnel) will resolve the issue without editing `/etc/hosts`.