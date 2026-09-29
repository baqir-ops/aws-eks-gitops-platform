# Secure GitOps Task API Helm Chart

A reusable and security-focused Helm chart for deploying the Secure GitOps
Task API to Kubernetes.

## Security controls

- Runs as non-root UID/GID `10001`
- Read-only container root filesystem
- Linux capabilities dropped
- Privilege escalation disabled
- RuntimeDefault seccomp profile
- Service account token automount disabled
- Explicit resource requests and limits
- Liveness and readiness probes
- Writable `/tmp` provided through an `emptyDir` volume
- Immutable image tag or digest support

## Chart location

    charts/task-api

## Validate

    helm lint charts/task-api --strict

    helm template task-api charts/task-api \
      --namespace dev \
      --values examples/values-dev.yaml

## Install

    helm upgrade --install task-api charts/task-api \
      --namespace dev \
      --create-namespace \
      --values examples/values-dev.yaml

## Optional features

- Horizontal Pod Autoscaler
- Prometheus Operator ServiceMonitor
- Kubernetes Ingress
- Image digest-based deployment
