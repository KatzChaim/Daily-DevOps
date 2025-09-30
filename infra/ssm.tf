# אפשר לקבע סביבה או לקרוא מ-workspace
variable "env" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

locals {
  ssm_param_name = "/eks/${var.env}/cluster_name"
}

resource "aws_ssm_parameter" "eks_cluster_name" {
  name      = local.ssm_param_name
  type      = "String"
  value     = module.eks.cluster_name # או aws_eks_cluster.this.name
  overwrite = true
}
