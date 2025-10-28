"""
Terraform Outputs for AWS SIP Trunk Deployment
"""

output "asterisk_instance_id" {
  description = "EC2 instance ID for primary Asterisk server"
  value       = aws_instance.asterisk.id
}

output "asterisk_private_ip" {
  description = "Private IP address of Asterisk server"
  value       = aws_instance.asterisk.private_ip
}

output "asterisk_public_ip" {
  description = "Elastic IP address for SIP endpoint"
  value       = aws_eip.asterisk.public_ip
}

output "sip_endpoint" {
  description = "SIP endpoint URI"
  value       = "sip:${aws_eip.asterisk.public_ip}:${local.sip_tcp_port}"
}

output "sip_domain" {
  description = "SIP domain name (if configured)"
  value       = var.domain_name != "" ? var.domain_name : "N/A"
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "security_group_id" {
  description = "Security group ID for Asterisk server"
  value       = aws_security_group.asterisk.id
}

output "recordings_bucket" {
  description = "S3 bucket name for call recordings"
  value       = aws_s3_bucket.recordings.id
}

output "recordings_bucket_arn" {
  description = "S3 bucket ARN for call recordings"
  value       = aws_s3_bucket.recordings.arn
}

output "backups_bucket" {
  description = "S3 bucket name for configuration backups"
  value       = var.backup_enabled ? aws_s3_bucket.backups[0].id : "N/A"
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.asterisk.name
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.asterisk.dashboard_name}"
}

output "ssh_command" {
  description = "SSH command to connect to Asterisk server"
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ec2-user@${aws_eip.asterisk.public_ip}"
}

output "asterisk_cli_command" {
  description = "Command to access Asterisk CLI"
  value       = "sudo asterisk -rx"
}

output "parameter_store_prefix" {
  description = "Parameter Store prefix for credentials"
  value       = "/${var.project_name}/"
}

output "rtp_port_range" {
  description = "RTP port range configured"
  value       = "${local.rtp_port_start}-${local.rtp_port_end}"
}

output "high_availability_enabled" {
  description = "Whether HA is enabled"
  value       = var.enable_high_availability
}

output "standby_instance_id" {
  description = "Standby instance ID (if HA enabled)"
  value       = var.enable_high_availability ? aws_instance.asterisk_standby[0].id : "N/A"
}

output "deployment_summary" {
  description = "Deployment summary"
  value = {
    project_name               = var.project_name
    environment                = var.environment
    region                     = var.aws_region
    sip_endpoint               = "sip:${aws_eip.asterisk.public_ip}:${local.sip_tcp_port}"
    instance_type              = var.instance_type
    asterisk_version           = "21"
    call_recordings_enabled    = var.enable_call_recordings
    cloudwatch_enabled         = var.enable_cloudwatch_monitoring
    high_availability          = var.enable_high_availability
    tls_enabled                = var.enable_tls
  }
}

# Sensitive outputs
output "elevenlabs_phone_parameter" {
  description = "Parameter Store path for ElevenLabs phone"
  value       = aws_ssm_parameter.elevenlabs_phone.name
  sensitive   = true
}

output "elevenlabs_password_parameter" {
  description = "Parameter Store path for ElevenLabs SIP password"
  value       = aws_ssm_parameter.elevenlabs_password.name
  sensitive   = true
}
