# Runbook

## Terraform workflow

```bash
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
terraform apply
```

Destroy (lab is disposable — always plan first):
```bash
terraform plan -destroy
terraform destroy
```

## EKS access

```bash
aws eks update-kubeconfig --region ap-south-1 --name secure-gitops-cluster
kubectl get nodes
kubectl get applications -n argocd
kubectl get pods -n monitoring
kubectl get servicemonitor -A
```

## Troubleshooting: kubectl cannot connect to EKS

Public IP changed and is no longer in the allowed CIDR.

```bash
curl https://api.ipify.org
aws eks describe-cluster --name secure-gitops-cluster --region ap-south-1 \
  --query "cluster.resourcesVpcConfig.publicAccessCidrs"

aws eks update-cluster-config --region ap-south-1 --name secure-gitops-cluster \
  --resources-vpc-config endpointPublicAccess=true,publicAccessCidrs="YOUR_PUBLIC_IP/32"

aws eks update-kubeconfig --region ap-south-1 --name secure-gitops-cluster
kubectl get nodes
```

Symptom if not fixed: `dial tcp <EKS_ENDPOINT>:443: i/o timeout`

## Terraform state security

```bash
git ls-files | grep -E 'terraform\.tfstate' || echo "No Terraform state tracked"
git check-ignore -v terraform.tfstate bootstrap/terraform.tfstate bootstrap/terraform.tfstate.backup
```

## Unexpected plan changes

Never run `terraform apply` blind. Run `terraform plan`, check for `destroy` /
`replace` on: EKS cluster, node groups, VPC, IAM roles, security groups, ECR, KMS.

## Final validation checklist

**Infrastructure:** fmt passes · validate passes · plan reviewed · no state tracked
· no secrets committed · EKS security reviewed · node volumes encrypted · IAM reviewed

**Git:** working tree clean · feature branches + PRs used · main branch protected
· CI checks passing

**Kubernetes:** cluster healthy · nodes Ready · Argo CD healthy/synced · monitoring
healthy · metrics available

**Cost control:** final evidence captured · destroy plan reviewed · lab destroyed
when no longer required

## Cost management

Lab infra generates AWS cost even when idle. Before destroying, capture evidence,
verify repos are pushed, and confirm no required resources will be lost.
