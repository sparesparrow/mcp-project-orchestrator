"""
VPC and Network Configuration for SIP Trunk
Creates VPC, subnets, security groups, and Elastic IP
"""

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-igw"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
    Tier = "Public"
  })
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-public-rt"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Elastic IP for SIP Endpoint
resource "aws_eip" "asterisk" {
  domain = "vpc"
  
  tags = merge(local.common_tags, {
    Name    = "${var.project_name}-eip"
    Purpose = "SIP-Endpoint"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# Secondary Elastic IP for HA (if enabled)
resource "aws_eip" "asterisk_standby" {
  count  = var.enable_high_availability ? 1 : 0
  domain = "vpc"
  
  tags = merge(local.common_tags, {
    Name    = "${var.project_name}-eip-standby"
    Purpose = "SIP-Endpoint-Standby"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# Security Group for Asterisk
resource "aws_security_group" "asterisk" {
  name_description = "${var.project_name}-asterisk-sg"
  description      = "Security group for Asterisk SIP trunk server"
  vpc_id           = aws_vpc.main.id
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-asterisk-sg"
  })
}

# SSH Access (restricted)
resource "aws_security_group_rule" "ssh" {
  count             = length(var.allowed_ssh_cidrs) > 0 ? 1 : 0
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = var.allowed_ssh_cidrs
  security_group_id = aws_security_group.asterisk.id
  description       = "SSH access from allowed CIDRs"
}

# SIP TCP Port
resource "aws_security_group_rule" "sip_tcp" {
  type              = "ingress"
  from_port         = local.sip_tcp_port
  to_port           = local.sip_tcp_port
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.asterisk.id
  description       = "SIP TCP signaling from ElevenLabs"
}

# SIP UDP Port (optional, for UDP transport)
resource "aws_security_group_rule" "sip_udp" {
  type              = "ingress"
  from_port         = local.sip_tcp_port
  to_port           = local.sip_tcp_port
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.asterisk.id
  description       = "SIP UDP signaling (optional)"
}

# RTP Media Ports
resource "aws_security_group_rule" "rtp" {
  type              = "ingress"
  from_port         = local.rtp_port_start
  to_port           = local.rtp_port_end
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.asterisk.id
  description       = "RTP media streams"
}

# TLS SIP Port (if enabled)
resource "aws_security_group_rule" "sip_tls" {
  count             = var.enable_tls ? 1 : 0
  type              = "ingress"
  from_port         = 5061
  to_port           = 5061
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.asterisk.id
  description       = "SIP TLS signaling"
}

# Egress - Allow all outbound traffic
resource "aws_security_group_rule" "egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.asterisk.id
  description       = "Allow all outbound traffic"
}

# Route 53 DNS Configuration (optional)
resource "aws_route53_record" "sip_srv" {
  count   = var.route53_zone_id != "" && var.domain_name != "" ? 1 : 0
  zone_id = var.route53_zone_id
  name    = "_sip._tcp.${var.domain_name}"
  type    = "SRV"
  ttl     = 300
  
  records = [
    "10 50 ${local.sip_tcp_port} ${var.domain_name}"
  ]
}

resource "aws_route53_record" "sip_a" {
  count   = var.route53_zone_id != "" && var.domain_name != "" ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 300
  records = [aws_eip.asterisk.public_ip]
}
