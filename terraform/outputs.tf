output "vpc_id" {
  description = "VPC identifier"
  value       = module.vpc.vpc_id
}

output "eks_cluster_endpoint" {
  description = "EKS Cluster API server endpoint"
  value       = module.kubernetes.cluster_endpoint
}

output "rds_endpoint" {
  description = "PostgreSQL primary write endpoint"
  value       = module.database.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary configuration endpoint"
  value       = module.redis.endpoint
}

output "s3_media_bucket" {
  description = "S3 bucket for clinical media and radiographs"
  value       = module.storage.media_bucket_name
}
