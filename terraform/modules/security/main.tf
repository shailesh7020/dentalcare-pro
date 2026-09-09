variable "environment" { type = string }
variable "vpc_id" { type = string }

resource "aws_security_group" "db" {
  name        = "dentalcare-db-sg-${var.environment}"
  description = "PostgreSQL access restricted to EKS pods"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.100.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "redis" {
  name        = "dentalcare-redis-sg-${var.environment}"
  description = "Redis access restricted to EKS pods"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.100.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "db_security_group_id" { value = aws_security_group.db.id }
output "redis_security_group_id" { value = aws_security_group.redis.id }
