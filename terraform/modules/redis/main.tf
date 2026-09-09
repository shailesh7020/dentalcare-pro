variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnets" { type = list(string) }
variable "redis_security_group_id" { type = string }
variable "node_type" { type = string }

resource "aws_elasticache_subnet_group" "redis" {
  name       = "dentalcare-redis-subnet-${var.environment}"
  subnet_ids = var.private_subnets
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "dentalcare-redis-${var.environment}"
  description                = "DentalCare High Availability Redis Cluster"
  node_type                  = var.node_type
  num_cache_clusters         = 2
  port                       = 6379
  parameter_group_name       = "default.redis7"
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [var.redis_security_group_id]
  automatic_failover_enabled = true
  multi_az_enabled           = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token_update_strategy = "ROTATE"
}

output "endpoint" { value = aws_elasticache_replication_group.redis.primary_endpoint_address }
