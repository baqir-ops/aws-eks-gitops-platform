provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "bootstrap"
      ManagedBy   = "terraform"
      Owner       = "baqir"
    }
  }
}

data "aws_caller_identity" "current" {}
