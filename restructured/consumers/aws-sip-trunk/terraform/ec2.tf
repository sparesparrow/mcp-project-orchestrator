"""
EC2 Instance Configuration for Asterisk SIP Server
"""

# IAM Role for EC2 Instance
resource "aws_iam_role" "asterisk" {
  name = "${var.project_name}-asterisk-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# IAM Policy for CloudWatch, S3, and Parameter Store
resource "aws_iam_role_policy" "asterisk" {
  name = "${var.project_name}-asterisk-policy"
  role = aws_iam_role.asterisk.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.recordings.arn,
          "${aws_s3_bucket.recordings.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/${var.project_name}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeAddresses",
          "ec2:AssociateAddress"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "asterisk" {
  name = "${var.project_name}-asterisk-profile"
  role = aws_iam_role.asterisk.name
  
  tags = local.common_tags
}

# User Data Script for Asterisk Installation
data "template_file" "user_data" {
  template = file("${path.module}/../scripts/user-data.sh")
  
  vars = {
    aws_region                = var.aws_region
    elastic_ip                = aws_eip.asterisk.public_ip
    elevenlabs_phone_e164     = var.elevenlabs_phone_e164
    project_name              = var.project_name
    enable_call_recordings    = var.enable_call_recordings
    s3_bucket_recordings      = aws_s3_bucket.recordings.id
    asterisk_log_level        = var.asterisk_log_level
    rtp_port_start            = local.rtp_port_start
    rtp_port_end              = local.rtp_port_end
    enable_cloudwatch         = var.enable_cloudwatch_monitoring
  }
}

# Primary Asterisk EC2 Instance
resource "aws_instance" "asterisk" {
  ami                         = data.aws_ami.amazon_linux_2.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.asterisk.id]
  iam_instance_profile        = aws_iam_instance_profile.asterisk.name
  key_name                    = var.ssh_key_name
  user_data                   = data.template_file.user_data.rendered
  associate_public_ip_address = true
  monitoring                  = var.enable_cloudwatch_monitoring
  
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    delete_on_termination = true
    encrypted             = true
    
    tags = merge(local.common_tags, {
      Name = "${var.project_name}-root-volume"
    })
  }
  
  # Additional volume for call recordings (if enabled)
  dynamic "ebs_block_device" {
    for_each = var.enable_call_recordings ? [1] : []
    content {
      device_name           = "/dev/sdf"
      volume_type           = "gp3"
      volume_size           = 100
      delete_on_termination = false
      encrypted             = true
      
      tags = merge(local.common_tags, {
        Name = "${var.project_name}-recordings-volume"
      })
    }
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-asterisk-primary"
    Role = "Primary"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# Associate Elastic IP
resource "aws_eip_association" "asterisk" {
  instance_id   = aws_instance.asterisk.id
  allocation_id = aws_eip.asterisk.id
}

# Standby Asterisk Instance (for HA)
resource "aws_instance" "asterisk_standby" {
  count                       = var.enable_high_availability ? 1 : 0
  ami                         = data.aws_ami.amazon_linux_2.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public[1].id
  vpc_security_group_ids      = [aws_security_group.asterisk.id]
  iam_instance_profile        = aws_iam_instance_profile.asterisk.name
  key_name                    = var.ssh_key_name
  user_data                   = data.template_file.user_data.rendered
  associate_public_ip_address = true
  monitoring                  = var.enable_cloudwatch_monitoring
  
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    delete_on_termination = true
    encrypted             = true
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-asterisk-standby"
    Role = "Standby"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# CloudWatch Log Group for Asterisk
resource "aws_cloudwatch_log_group" "asterisk" {
  name              = "/aws/ec2/${var.project_name}/asterisk"
  retention_in_days = 30
  
  tags = local.common_tags
}
