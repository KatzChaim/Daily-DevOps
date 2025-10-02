module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"

  # IPv4
  cidr = "10.100.0.0/16"

  # AZs + Subnets
  azs             = ["${var.region}a", "${var.region}b"]
  private_subnets = ["10.100.1.0/24", "10.100.2.0/24"]
  public_subnets  = ["10.100.101.0/24", "10.100.102.0/24"]

  # --- IPv6 ON ---
  enable_ipv6 = true

  # הקצה כתובות IPv6 אוטומטית ל־ENI בסאבנטים
  public_subnet_assign_ipv6_address_on_creation  = true
  private_subnet_assign_ipv6_address_on_creation = true

  # לכל סאבנט צריך prefix-index ייחודי (לפי מספר הסאבנטים)
  public_subnet_ipv6_prefixes  = [0, 1]
  private_subnet_ipv6_prefixes = [2, 3]

  # יצירת egress-only IGW ל־IPv6 (לגלישה החוצה בלבד מהפרטיים)
  create_egress_only_igw = true

  # NAT ל־IPv4 
  enable_nat_gateway = true
  single_nat_gateway = true

  # תגיות ל־EKS LoadBalancers
  public_subnet_tags  = { "kubernetes.io/role/elb"          = "1" }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = "1" }
}
