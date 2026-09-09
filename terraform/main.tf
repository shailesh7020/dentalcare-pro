terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
  }

  backend "s3" {
    bucket         = "dentalcare-terraform-state-prod"
    key            = "production/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "dentalcare-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "DentalCare Pro"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

module "vpc" {
  source       = "./modules/vpc"
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  cluster_name = var.cluster_name
}

module "security" {
  source      = "./modules/security"
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
}

module "storage" {
  source      = "./modules/storage"
  environment = var.environment
}

module "database" {
  source               = "./modules/database"
  environment          = var.environment
  vpc_id               = module.vpc.vpc_id
  database_subnets     = module.vpc.database_subnets
  db_security_group_id = module.security.db_security_group_id
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
}

module "redis" {
  source                  = "./modules/redis"
  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  private_subnets         = module.vpc.private_subnets
  redis_security_group_id = module.security.redis_security_group_id
  node_type               = var.redis_node_type
}

module "kubernetes" {
  source          = "./modules/kubernetes"
  environment     = var.environment
  cluster_name    = var.cluster_name
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
}
