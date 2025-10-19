"""
Terraform Variables for AWS SIP Trunk Deployment
"""

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "asterisk-sip-trunk"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "instance_type" {
  description = "EC2 instance type for Asterisk server"
  type        = string
  default     = "t3.medium"
  
  validation {
    condition     = can(regex("^t3\\.(small|medium|large)$", var.instance_type))
    error_message = "Instance type must be t3.small, t3.medium, or t3.large for VoIP workloads."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "enable_high_availability" {
  description = "Enable HA with active-standby configuration"
  type        = bool
  default     = false
}

variable "ssh_key_name" {
  description = "SSH key pair name for EC2 access"
  type        = string
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = []  # Empty by default for security
}

variable "elevenlabs_phone_e164" {
  description = "ElevenLabs phone number in E.164 format"
  type        = string
  sensitive   = true
  
  validation {
    condition     = can(regex("^\\+[1-9]\\d{1,14}$", var.elevenlabs_phone_e164))
    error_message = "Phone number must be in E.164 format (+12025551234)."
  }
}

variable "elevenlabs_sip_password" {
  description = "ElevenLabs SIP trunk password"
  type        = string
  sensitive   = true
}

variable "enable_call_recordings" {
  description = "Enable call recording to S3"
  type        = bool
  default     = true
}

variable "call_recording_retention_days" {
  description = "Days to retain call recordings in S3"
  type        = number
  default     = 90
}

variable "enable_cloudwatch_monitoring" {
  description = "Enable CloudWatch detailed monitoring"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarms"
  type        = string
  default     = ""
}

variable "asterisk_log_level" {
  description = "Asterisk logging level (ERROR, WARNING, NOTICE, VERBOSE, DEBUG)"
  type        = string
  default     = "NOTICE"
  
  validation {
    condition     = contains(["ERROR", "WARNING", "NOTICE", "VERBOSE", "DEBUG"], var.asterisk_log_level)
    error_message = "Log level must be ERROR, WARNING, NOTICE, VERBOSE, or DEBUG."
  }
}

variable "enable_tls" {
  description = "Enable TLS for SIP transport"
  type        = bool
  default     = false
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID for SIP SRV records (optional)"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for SIP endpoint (e.g., sip.example.com)"
  type        = string
  default     = ""
}

variable "backup_enabled" {
  description = "Enable automated backups to S3"
  type        = bool
  default     = true
}

variable "backup_schedule" {
  description = "Cron schedule for configuration backups"
  type        = string
  default     = "0 2 * * *"  # 2 AM daily
}
