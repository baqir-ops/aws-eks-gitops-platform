variable "aws_region" {
  description = "AWS region for Amazon ECR"
  type        = string
  default     = "ap-south-1"
}

variable "github_owner" {
  description = "GitHub organization or user that owns the application repository"
  type        = string
  default     = "baqir-ops"
}

variable "github_repository" {
  description = "GitHub repository allowed to assume the AWS role"
  type        = string
  default     = "secure-gitops-app"
}

variable "github_branch" {
  description = "GitHub branch allowed to assume the AWS role"
  type        = string
  default     = "main"
}

variable "ecr_repository_name" {
  description = "Private Amazon ECR repository name"
  type        = string
  default     = "secure-gitops-app"
}

variable "ecr_image_retention_count" {
  description = "Maximum number of container images retained in ECR"
  type        = number
  default     = 20

  validation {
    condition     = var.ecr_image_retention_count >= 5
    error_message = "ECR image retention must be at least 5."
  }
}
