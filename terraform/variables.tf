variable "environment" {
  type        = string
  description = "Target deployment environment (development, staging, production)"
  default     = "production"
}

variable "aws_region" {
  type        = string
  description = "AWS Region for infrastructure deployment"
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  type        = string
  description = "Primary CIDR block for VPC"
  default     = "10.100.0.0/16"
}

variable "cluster_name" {
  type        = string
  description = "Kubernetes EKS cluster name"
  default     = "dentalcare-eks-prod"
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance size"
  default     = "db.r6g.xlarge"
}

variable "db_allocated_storage" {
  type        = number
  description = "Initial allocated storage in GB"
  default     = 250
}

variable "redis_node_type" {
  type        = string
  description = "ElastiCache node type"
  default     = "cache.r6g.large"
}

variable "domain_name" {
  type        = string
  description = "Base domain name for SSL and Ingress"
  default     = "dentalcarepro.com"
}
