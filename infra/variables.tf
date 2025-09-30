variable "project_name" {
  description = "Project prefix"
  type        = string
  default     = "fm"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "eks_version" {
  description = "EKS version"
  type        = string
  default     = "1.30"
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 6
}

variable "instance_types" {
  description = "Node types"
  type        = list(string)
  default     = ["t3a.small"]
}
