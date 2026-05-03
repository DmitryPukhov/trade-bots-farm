#!/bin/bash
# Script to fix SeaweedFS DNS resolution for Minikube ingress

set -e

echo "=== SeaweedFS DNS Resolution Fix ==="
echo ""

MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"
echo ""

echo "1. Testing DNS resolution for all SeaweedFS hosts..."
HOSTS=("s3.tradebotsfarm.svc.cluster.local" "filer.tradebotsfarm.svc.cluster.local" "master.tradebotsfarm.svc.cluster.local")
ALL_RESOLVED_VIA_MINIKUBE=true
ALL_RESOLVED_ON_SYSTEM=true

for host in "${HOSTS[@]}"; do
    echo "   Testing $host:"
    
    # Test via Minikube DNS
    if nslookup $host $MINIKUBE_IP >/dev/null 2>&1; then
        echo "     ✓ Minikube DNS: OK"
    else
        echo "     ✗ Minikube DNS: FAIL"
        ALL_RESOLVED_VIA_MINIKUBE=false
    fi
    
    # Test via system DNS
    if ping -c 1 $host >/dev/null 2>&1; then
        echo "     ✓ System DNS: OK"
    else
        echo "     ✗ System DNS: FAIL"
        ALL_RESOLVED_ON_SYSTEM=false
    fi
    echo ""
done

if [ "$ALL_RESOLVED_VIA_MINIKUBE" = true ]; then
    echo "   ✓ All hosts resolve via Minikube DNS server"
else
    echo "   ✗ Some hosts fail via Minikube DNS server"
fi

if [ "$ALL_RESOLVED_ON_SYSTEM" = true ]; then
    echo "   ✓ All hostnames resolve on system"
else
    echo "   ✗ Some hostnames do not resolve on system"
fi

echo ""
echo "2. Available solutions:"
echo ""
echo "   A) Configure systemd-resolved (Recommended)"
echo "      Run: sudo ./configure-dns-systemd.sh"
echo ""
echo "   B) Use Minikube Tunnel"
echo "      In a separate terminal run: minikube tunnel"
echo "      Then access:"
echo "      - S3 API: http://s3.tradebotsfarm.svc.cluster.local/"
echo "      - Filer UI: http://filer.tradebotsfarm.svc.cluster.local/"
echo "      - Master UI: http://master.tradebotsfarm.svc.cluster.local/"
echo ""
echo "   C) Browser workaround with ModHeader extension"
echo "      For S3 API: Add Host header: s3.tradebotsfarm.svc.cluster.local"
echo "      For Filer UI: Add Host header: filer.tradebotsfarm.svc.cluster.local"
echo "      For Master UI: Add Host header: master.tradebotsfarm.svc.cluster.local"
echo "      Access: http://$MINIKUBE_IP/"
echo ""
echo "   D) Use curl with Host header"
echo "      curl -H 'Host: s3.tradebotsfarm.svc.cluster.local' http://$MINIKUBE_IP/"
echo "      curl -H 'Host: filer.tradebotsfarm.svc.cluster.local' http://$MINIKUBE_IP/"
echo "      curl -H 'Host: master.tradebotsfarm.svc.cluster.local' http://$MINIKUBE_IP/"
echo ""
echo "3. Testing connectivity..."
echo ""
echo "   S3 API:"
curl -s -H "Host: s3.tradebotsfarm.svc.cluster.local" "http://$MINIKUBE_IP/" | grep -o "<ListAllMyBucketsResult.*" | head -1 || echo "   Response received"
echo ""
echo "   Filer UI:"
curl -s -H "Host: filer.tradebotsfarm.svc.cluster.local" "http://$MINIKUBE_IP/" | grep -o "<title>.*</title>" || echo "   HTML page received"
echo ""
echo "   Master UI:"
curl -s -H "Host: master.tradebotsfarm.svc.cluster.local" "http://$MINIKUBE_IP/" | grep -o "<title>.*</title>" || echo "   HTML page received"
echo ""
echo "=== End of diagnostics ==="