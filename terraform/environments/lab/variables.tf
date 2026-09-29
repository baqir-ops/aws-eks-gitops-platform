variable "aws_region" {
  description = "AWS region where infrastructure will be created"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name used for naming and tagging resources"
  type        = string
  default     = "secure-gitops-platform"
}

variable "environment" {
  description = "Environment name used for tagging"
  type        = string
  default     = "lab"
}

variable "cluster_name" {
  description = "Name of the Amazon EKS cluster"
  type        = string
  default     = "secure-gitops-cluster"
}

variable "cluster_version" {
  description = "Kubernetes version currently in EKS standard support"
  type        = string
  default     = "1.35"
}

variable "node_instance_types" {
  description = "EC2 instance types used by the EKS managed node group"
  type        = list(string)
  default     = ["t3.large"]
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "CIDR blocks permitted to access the public Kubernetes API endpoint"
  type        = list(string)
}
