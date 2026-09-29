output "aws_account_id" {
  description = "AWS account containing the OIDC role and ECR repository"
  value       = data.aws_caller_identity.current.account_id
}

output "github_oidc_provider_arn" {
  description = "AWS IAM GitHub OIDC provider ARN"
  value       = aws_iam_openid_connect_provider.github.arn
}

output "github_actions_role_arn" {
  description = "Role assumed by the GitHub Actions workflow"
  value       = aws_iam_role.github_actions_ecr.arn
}

output "github_oidc_subject" {
  description = "Exact GitHub repository and branch allowed by the trust policy"
  value       = local.github_subject
}

output "ecr_repository_arn" {
  description = "Amazon ECR repository ARN"
  value       = aws_ecr_repository.app.arn
}

output "ecr_repository_url" {
  description = "Amazon ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}
