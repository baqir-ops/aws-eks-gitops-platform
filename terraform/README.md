# Secure GitOps Infrastructure

[![Terraform Validation](https://github.com/baqir-ops/secure-gitops-infrastructure/actions/workflows/terraform-validation.yml/badge.svg)](https://github.com/baqir-ops/secure-gitops-infrastructure/actions/workflows/terraform-validation.yml)

Terraform infrastructure for the Secure GitOps Platform running on AWS EKS.

Provisions the AWS layer — networking, EKS, IAM, ECR, and encryption — for a
GitOps-driven Kubernetes platform. Kubernetes application delivery is managed
separately by Argo CD (see [Related Repositories](#related-repositories)).

## Architecture

```
Internet
   |
   v
VPC (10.20.0.0/16) — 2 AZs, no NAT Gateway (cost-conscious lab design)
   |
   v
Amazon EKS (secure-gitops-cluster, ap-south-1)
   |
   +-- Managed node group (t3.large)
   +-- Add-ons: CoreDNS, VPC CNI, kube-proxy, EBS CSI, Pod Identity
   |
   v
Argo CD  -->  dev / staging / production
```

- VPC CIDR: `10.20.0.0/16` | Public subnets: `10.20.1.0/24`, `10.20.2.0/24`
- EKS public API access restricted to an explicit `/32` CIDR
- No NAT Gateway — deliberate cost tradeoff for a disposable lab environment

## Repository structure

```
bootstrap/            # Remote state backend
environments/lab/      # VPC, EKS, IAM, ECR, network
environments/github-oidc-ecr/   # GitHub Actions OIDC trust + ECR
docs/screenshots/
docs/RUNBOOK.md         # Full command reference & troubleshooting
```

## Deploy

```bash
cd environments/lab
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
terraform apply
```

Verify:
```bash
aws eks update-kubeconfig --region ap-south-1 --name secure-gitops-cluster
kubectl get nodes
kubectl get applications -n argocd
```

## Security controls

- **GitHub OIDC** — GitHub Actions authenticates to AWS via short-lived tokens; no long-lived access keys stored in CI
- **Least-privilege IAM** — no wildcard `Action = "*"` policies
- **Encrypted EBS volumes** via AWS KMS
- **Restricted EKS API access** to a single administrator CIDR
- **No Terraform state committed** — verified via `git ls-files | grep tfstate`
- **No secrets committed** — AWS Secrets Manager / SSM Parameter Store / GitHub Actions Secrets used instead

Full checklist and troubleshooting steps: [`docs/RUNBOOK.md`](docs/RUNBOOK.md)

## Screenshots

**Terraform apply — infrastructure provisioned successfully**
![Terraform apply success](docs/screenshots/phase-02/phase-02-01-terraform-apply-success.png)

**EKS nodes healthy and Ready**
![EKS nodes ready](docs/screenshots/phase-02/phase-02-02-eks-node-ready.png)

**GitHub OIDC trust policy + ECR security settings**
![OIDC trust and ECR security](docs/screenshots/phase-06/phase-06-02-oidc-trust-and-ecr-security.png)

## Related repositories

| Repo | Purpose |
|---|---|
| [secure-gitops-app](https://github.com/baqir-ops/secure-gitops-app) | Application source, Dockerfile, app CI/CD |
| [secure-gitops-platform](https://github.com/baqir-ops/secure-gitops-platform) | Argo CD config, ApplicationSets, monitoring |
| [secure-gitops-helm-chart](https://github.com/baqir-ops/secure-gitops-helm-chart) | Helm chart, K8s templates |

## Status

This is a lab/portfolio environment, not a system under live production traffic.
It follows production-style practices (IaC, GitOps, OIDC, least privilege,
disposable infra) at a scale intended for demonstration and cost control.

## Author

Muhammad Baqir Nawaz — Cloud / DevOps Engineer — [github.com/baqir-ops](https://github.com/baqir-ops)
