output "cluster_name" {
  description = "Amazon EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Amazon EKS Kubernetes API endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "Kubernetes version used by the EKS cluster"
  value       = module.eks.cluster_version
}

output "cluster_oidc_provider_arn" {
  description = "OIDC provider ARN created for IRSA"
  value       = module.eks.oidc_provider_arn
}

output "ecr_repository_url" {
  description = "Amazon ECR repository URL for the application"
  value       = data.aws_ecr_repository.app.repository_url
}

output "ebs_csi_role_arn" {
  description = "IAM role used by the EBS CSI controller through Pod Identity"
  value       = aws_iam_role.ebs_csi.arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs used by EKS"
  value       = module.vpc.public_subnets
}
