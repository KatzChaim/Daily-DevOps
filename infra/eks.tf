module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.20"

  # Cluster basics
  cluster_name                   = "${var.project_name}-eks"
  cluster_version                = var.eks_version
  cluster_endpoint_public_access = true
  enable_irsa                    = true

  # Networking
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Managed node group
  eks_managed_node_groups = {
    default = {
      instance_types = var.instance_types
      desired_size   = var.node_desired_size
      min_size       = var.node_min_size
      max_size       = var.node_max_size
      ami_type       = "AL2_x86_64"
    }
  }

  # Give your IAM user admin (kubectl) permissions inside the cluster
  manage_aws_auth = true
  aws_auth_users = [
    {
      userarn  = "arn:aws:iam::640168441859:user/Chaim"  # your IAM user ARN
      username = "chaim"
      groups   = ["system:masters"]
    }
  ]

  tags = { Project = var.project_name }
}
