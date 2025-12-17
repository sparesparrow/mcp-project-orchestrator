"""
AWS SIP Trunk Infrastructure for ElevenLabs Integration
Terraform configuration for deploying Asterisk PBX on EC2
"""

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Configure backend for state management
    # bucket = "your-terraform-state-bucket"
    # key    = "asterisk-sip-trunk/terraform.tfstate"
    # region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Purpose     = "SIP-Trunk-ElevenLabs"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Local variables
locals {
  common_tags = {
    Name        = "${var.project_name}-${var.environment}"
    Component   = "SIP-Trunk"
    Integration = "ElevenLabs"
  }
  
  asterisk_version = "21"
  sip_tcp_port    = 5060
  rtp_port_start  = 10000
  rtp_port_end    = 20000
}
