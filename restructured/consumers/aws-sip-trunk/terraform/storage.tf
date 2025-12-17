"""
Storage Configuration for Call Recordings and Configuration Backups
"""

# S3 Bucket for Call Recordings
resource "aws_s3_bucket" "recordings" {
  bucket = "${var.project_name}-recordings-${data.aws_caller_identity.current.account_id}"
  
  tags = merge(local.common_tags, {
    Name    = "${var.project_name}-recordings"
    Purpose = "CallRecordings"
  })
}

# Bucket Versioning
resource "aws_s3_bucket_versioning" "recordings" {
  bucket = aws_s3_bucket.recordings.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "recordings" {
  bucket = aws_s3_bucket.recordings.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Lifecycle Policy for Recordings
resource "aws_s3_bucket_lifecycle_configuration" "recordings" {
  bucket = aws_s3_bucket.recordings.id
  
  rule {
    id     = "archive-old-recordings"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = var.call_recording_retention_days
    }
  }
}

# Block Public Access
resource "aws_s3_bucket_public_access_block" "recordings" {
  bucket = aws_s3_bucket.recordings.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for Configuration Backups
resource "aws_s3_bucket" "backups" {
  count  = var.backup_enabled ? 1 : 0
  bucket = "${var.project_name}-backups-${data.aws_caller_identity.current.account_id}"
  
  tags = merge(local.common_tags, {
    Name    = "${var.project_name}-backups"
    Purpose = "ConfigurationBackups"
  })
}

resource "aws_s3_bucket_versioning" "backups" {
  count  = var.backup_enabled ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Systems Manager Parameter Store for Credentials
resource "aws_ssm_parameter" "elevenlabs_phone" {
  name        = "/${var.project_name}/elevenlabs/phone_e164"
  description = "ElevenLabs phone number in E.164 format"
  type        = "SecureString"
  value       = var.elevenlabs_phone_e164
  
  tags = local.common_tags
}

resource "aws_ssm_parameter" "elevenlabs_password" {
  name        = "/${var.project_name}/elevenlabs/sip_password"
  description = "ElevenLabs SIP trunk password"
  type        = "SecureString"
  value       = var.elevenlabs_sip_password
  
  tags = local.common_tags
}

resource "aws_ssm_parameter" "elastic_ip" {
  name        = "/${var.project_name}/network/elastic_ip"
  description = "Elastic IP for SIP endpoint"
  type        = "String"
  value       = aws_eip.asterisk.public_ip
  
  tags = local.common_tags
}

# Data source for account ID
data "aws_caller_identity" "current" {}
