variable "db_password" {
  description = "RDS master password"
  sensitive   = true
}

variable "db_username" {
  default = "postgres"
}

# ── Subnet Group ───────────────────────────────────────────────────────────────
resource "aws_db_subnet_group" "justbuildit_db_subnet" {
  name       = "justbuildit-db-subnet"
  subnet_ids = [] # Fill in your subnet IDs
}

# ── RDS PostgreSQL ─────────────────────────────────────────────────────────────
resource "aws_db_instance" "justbuildit_postgres" {
  identifier             = "justbuildit-postgres"
  engine                 = "postgres"
  engine_version         = "16.2"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_encrypted      = true
  db_name                = "justbuildit"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.justbuildit_db_subnet.name
  publicly_accessible    = false
  skip_final_snapshot    = true
  deletion_protection    = false

  tags = {
    Name    = "justbuildit-postgres"
    Project = "justbuildit"
  }
}

output "rds_endpoint" {
  value = aws_db_instance.justbuildit_postgres.endpoint
}
