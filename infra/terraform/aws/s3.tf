resource "aws_s3_bucket" "justbuildit_assets" {
  bucket = "justbuildit-assets-${random_id.bucket_suffix.hex}"

  tags = {
    Name    = "justbuildit-assets"
    Project = "justbuildit"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_versioning" "assets_versioning" {
  bucket = aws_s3_bucket.justbuildit_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "assets_encryption" {
  bucket = aws_s3_bucket.justbuildit_assets.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

output "s3_bucket_name" {
  value = aws_s3_bucket.justbuildit_assets.bucket
}
