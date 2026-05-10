#!/bin/bash
set -x
helm template test seaweedfs/seaweedfs --version 4.21.0 --set filer.ingress.enabled=true --set filer.ingress.annotations.nginx\\.ingress\\.kubernetes\\.io/auth-type=basic 2>&1 | grep -A5 "annotations:"
