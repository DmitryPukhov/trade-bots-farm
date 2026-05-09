#!/bin/bash
# Quick test script for SeaweedFS s3cmd access

set -e

echo "=== SeaweedFS s3cmd Quick Test ==="
echo ""

# Check if s3cmd is installed
if ! command -v s3cmd &> /dev/null; then
    echo "ERROR: s3cmd is not installed. Install it with:"
    echo "  sudo apt-get install s3cmd  # Debian/Ubuntu"
    echo "  brew install s3cmd          # macOS"
    exit 1
fi

echo "1. Checking Minikube status..."
if ! minikube status &> /dev/null; then
    echo "   ✗ Minikube is not running. Start it with:"
    echo "     minikube start"
    exit 1
else
    echo "   ✓ Minikube is running"
fi

echo ""
echo "2. Checking SeaweedFS pods..."
if kubectl get pods -n trade-bots-farm | grep -q "seaweedfs.*Running"; then
    echo "   ✓ SeaweedFS pods are running"
else
    echo "   ✗ SeaweedFS pods not found or not running"
    echo "   Deploy SeaweedFS with:"
    echo "     cd k8s/terraform && terraform apply"
    exit 1
fi

echo ""
echo "3. Creating s3cmd configuration..."
cat > /tmp/test-seaweedfs-s3cfg << 'EOF'
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

echo "   Configuration saved to /tmp/test-seaweedfs-s3cfg"
echo ""

echo "4. Testing connection (this may take a moment)..."
if S3CMD_CONFIG=/tmp/test-seaweedfs-s3cfg s3cmd ls 2>/dev/null; then
    echo ""
    echo "   ✓ SUCCESS: Connected to SeaweedFS S3!"
    echo ""
    echo "5. Listing buckets:"
    S3CMD_CONFIG=/tmp/test-seaweedfs-s3cfg s3cmd ls
else
    echo ""
    echo "   ✗ Connection failed. Possible issues:"
    echo "     - DNS resolution for s3.tradebotsfarm.svc.cluster.local"
    echo "     - Minikube tunnel not running"
    echo ""
    echo "   Try starting minikube tunnel in another terminal:"
    echo "     minikube tunnel"
    echo ""
    echo "   Then run this test again."
    exit 1
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "To use s3cmd permanently, copy the configuration:"
echo "  cp /tmp/test-seaweedfs-s3cfg ~/.s3cfg"
echo ""
echo "Or run the interactive configuration:"
echo "  s3cmd --configure"
echo ""
echo "See SEAWEEDFS-S3CMD-ACCESS.md for detailed instructions."
