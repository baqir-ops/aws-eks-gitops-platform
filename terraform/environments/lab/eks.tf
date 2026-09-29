module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = var.cluster_version

  endpoint_private_access      = true
  endpoint_public_access       = true
  endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs

  enable_cluster_creator_admin_permissions = true
  enable_irsa                              = true

  upgrade_policy = {
    support_type = "STANDARD"
  }

  enabled_log_types = [
    "api",
    "audit",
    "authenticator"
  ]

  cloudwatch_log_group_retention_in_days = 7

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets

  addons = {
    coredns = {
      most_recent = true
    }

    "kube-proxy" = {
      most_recent = true
    }

    "vpc-cni" = {
      most_recent    = true
      before_compute = true
    }

    "eks-pod-identity-agent" = {
      most_recent    = true
      before_compute = true
    }

    "aws-ebs-csi-driver" = {
      most_recent = true

      pod_identity_association = [
        {
          role_arn        = aws_iam_role.ebs_csi.arn
          service_account = "ebs-csi-controller-sa"
        }
      ]
    }
  }

  eks_managed_node_groups = {
    general = {
      name = "general"

      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      min_size     = 1
      max_size     = 2
      desired_size = 1

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"

          ebs = {
            delete_on_termination = true
            encrypted             = true
            volume_size           = 30
            volume_type           = "gp3"
          }
        }
      }

      labels = {
        workload = "general"
      }

      iam_role_additional_policies = {
        ecr_readonly = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
      }
    }
  }
}
