provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "secure-gitops-platform"
      Environment = "shared"
      Component   = "github-oidc-ecr"
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}
