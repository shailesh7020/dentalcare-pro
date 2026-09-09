variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "database_subnets" { type = list(string) }
variable "db_security_group_id" { type = string }
variable "instance_class" { type = string }
variable "allocated_storage" { type = number }

resource "aws_db_subnet_group" "rds" {
  name       = "dentalcare-rds-subnet-group-${var.environment}"
  subnet_ids = var.database_subnets
}

resource "aws_kms_key" "db_kms" {
  description             = "KMS key for DentalCare PostgreSQL encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_db_instance" "postgresql" {
  identifier                  = "dentalcare-pg-${var.environment}"
  engine                      = "postgres"
  engine_version              = "17.1"
  instance_class              = var.instance_class
  allocated_storage           = var.allocated_storage
  max_allocated_storage       = 1000
  storage_type                = "gp3"
  storage_encrypted           = true
  kms_key_id                  = aws_kms_key.db_kms.arn
  multi_az                    = true
  db_name                     = "dentalcare"
  username                    = "dentaladmin"
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [var.db_security_group_id]

  backup_retention_period   = 30
  backup_window             = "01:00-02:00"
  maintenance_window        = "Sun:03:00-Sun:04:00"
  copy_tags_to_snapshot     = true
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "dentalcare-pg-final-snapshot"

  performance_insights_enabled    = true
  performance_insights_retention_period = 731
}

output "endpoint" { value = aws_db_instance.postgresql.endpoint }
