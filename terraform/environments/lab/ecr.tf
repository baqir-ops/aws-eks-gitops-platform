# The ECR repository is persistent and managed by the
# environments/github-oidc-ecr Terraform stack.
#
# This temporary EKS lab stack only reads and consumes it.
data "aws_ecr_repository" "app" {
  name = "secure-gitops-app"
}
