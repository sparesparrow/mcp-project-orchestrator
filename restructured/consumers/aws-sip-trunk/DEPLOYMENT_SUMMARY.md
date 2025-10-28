# AWS SIP Trunk Deployment Summary

## Project Overview

Complete infrastructure-as-code solution for deploying production-ready Asterisk SIP trunk on AWS EC2 with ElevenLabs conversational AI integration.

### Key Features

✅ **Automated Infrastructure Deployment**
- Terraform IaC for reproducible deployments
- VPC with public subnets and Internet Gateway
- EC2 instance with Asterisk 21 compiled from source
- Elastic IP for consistent SIP endpoint
- Security Groups with SIP/RTP port configuration

✅ **SIP Trunk Configuration**
- PJSIP protocol with TCP transport
- NAT traversal with external address configuration
- E.164 phone number authentication
- Codec negotiation (ulaw, alaw)
- RTP port range: 10000-20000

✅ **Monitoring & Observability**
- CloudWatch Logs for Asterisk full/message logs
- Custom metrics for SIP registration, call failures
- CloudWatch Dashboard with real-time metrics
- Automated alarms for CPU, memory, disk, SIP health
- SNS notifications for critical alerts

✅ **Security & Compliance**
- Minimal Security Group rules (SIP, RTP only)
- Credentials stored in Systems Manager Parameter Store (encrypted)
- Fail2Ban for SIP brute-force protection
- Optional TLS transport for encrypted signaling
- IAM roles with least-privilege access

✅ **Backup & Disaster Recovery**
- S3 buckets for call recordings and config backups
- Lifecycle policies for cost optimization
- Automated daily configuration backups
- High-availability mode with active-standby instances
- Elastic IP re-association on instance restart

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    VPC (10.0.0.0/16)                      │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │         Public Subnet (10.0.1.0/24)                 │ │ │
│  │  │                                                     │ │ │
│  │  │  ┌─────────────────────────────────────┐          │ │ │
│  │  │  │   EC2 Instance (t3.medium)          │          │ │ │
│  │  │  │   ┌─────────────────────────────┐   │          │ │ │
│  │  │  │   │   Asterisk 21 + PJSIP       │   │          │ │ │
│  │  │  │   │   - TCP Port: 5060          │   │          │ │ │
│  │  │  │   │   - RTP: 10000-20000        │   │          │ │ │
│  │  │  │   └─────────────────────────────┘   │          │ │ │
│  │  │  │   Private IP: 10.0.1.x              │          │ │ │
│  │  │  └─────────────────┬───────────────────┘          │ │ │
│  │  │                    │                              │ │ │
│  │  │                    │ Elastic IP                   │ │ │
│  │  │                    ▼                              │ │ │
│  │  │              18.xxx.xxx.xxx                       │ │ │
│  │  │                    │                              │ │ │
│  │  └────────────────────┼──────────────────────────────┘ │ │
│  │                       │                                │ │
│  │         Internet Gateway                              │ │
│  └───────────────────────┼────────────────────────────────┘ │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           │ SIP/RTP over Internet
                           │
                           ▼
              ┌────────────────────────┐
              │   ElevenLabs Platform   │
              │   sip.elevenlabs.io    │
              │   - Conversational AI   │
              │   - SIP Trunk          │
              └────────────────────────┘
```

## Directory Structure

```
aws-sip-trunk/
├── README.md                     # Main project documentation
├── QUICKSTART.md                 # 5-minute setup guide
├── DEPLOYMENT_SUMMARY.md         # This file
├── .gitignore                    # Git exclusions
├── pyproject.toml                # Python project metadata
│
├── terraform/                    # Infrastructure as Code
│   ├── main.tf                   # Main Terraform config
│   ├── variables.tf              # Input variables
│   ├── outputs.tf                # Export values
│   ├── networking.tf             # VPC, Security Groups, EIP
│   ├── ec2.tf                    # EC2 instances, IAM roles
│   ├── storage.tf                # S3, Parameter Store
│   ├── monitoring.tf             # CloudWatch alarms, dashboard
│   └── terraform.tfvars.example  # Example variables
│
├── scripts/                      # Deployment and utility scripts
│   ├── deploy-asterisk-aws.sh    # Manual deployment (AWS CLI)
│   └── user-data.sh              # EC2 bootstrap script
│
├── config/                       # Configuration templates
│   ├── pjsip.conf.j2             # PJSIP Jinja2 template
│   ├── extensions.conf.j2        # Dialplan Jinja2 template
│   └── rtp.conf                  # RTP configuration
│
├── docs/                         # Detailed documentation
│   ├── DEPLOYMENT.md             # Step-by-step deployment
│   └── TROUBLESHOOTING.md        # Issue resolution guide
│
└── tests/                        # Integration tests
    └── test_sip_connectivity.py  # SIP trunk tests
```

## Deployment Options

### Option 1: Terraform (Recommended)

**Pros:**
- Declarative infrastructure definition
- State management for updates
- Idempotent deployments
- Easy to version control
- Supports modules and reusability

**Deployment time:** 15-20 minutes

```bash
cd terraform
terraform init
terraform apply
```

### Option 2: Manual Script

**Pros:**
- No Terraform installation required
- Direct AWS CLI commands
- Easier to debug individual steps
- Good for one-time deployments

**Deployment time:** 20-25 minutes

```bash
cd scripts
./deploy-asterisk-aws.sh
```

## Configuration Files

### PJSIP Configuration (`pjsip.conf.j2`)

Jinja2 template supporting:
- Multiple transports (TCP, TLS, UDP)
- NAT traversal configuration
- Endpoint/AOR/Auth/Identify sections
- Codec preferences
- Session timers and qualify options
- Custom endpoints via template variables

### Dialplan Configuration (`extensions.conf.j2`)

Jinja2 template supporting:
- Inbound call handling
- Outbound call routing
- Call recording with S3 upload
- IVR menu system
- DTMF handling
- Hangup handlers
- Custom contexts

### Terraform Variables

**Required:**
- `aws_region`: AWS deployment region
- `ssh_key_name`: EC2 SSH key pair name
- `elevenlabs_phone_e164`: ElevenLabs phone (E.164)
- `elevenlabs_sip_password`: SIP trunk password

**Optional:**
- `instance_type`: EC2 size (default: t3.medium)
- `enable_high_availability`: Active-standby (default: false)
- `enable_call_recordings`: S3 recordings (default: true)
- `enable_cloudwatch_monitoring`: Detailed metrics (default: true)
- `alarm_email`: SNS notification email
- `route53_zone_id`: DNS configuration
- `enable_tls`: TLS transport

## AWS Resources Created

### Compute
- **EC2 Instance**: Amazon Linux 2, t3.medium, 30GB root EBS
- **Optional**: Additional 100GB EBS for recordings
- **Optional**: Standby EC2 instance for HA

### Networking
- **VPC**: /16 CIDR block
- **Subnet**: 2x public subnets in different AZs
- **Internet Gateway**: For public internet access
- **Route Tables**: Public routing
- **Elastic IP**: 1 primary (+ 1 standby for HA)
- **Security Group**: SIP/RTP/SSH rules

### Storage
- **S3 Bucket**: Call recordings (with lifecycle policies)
- **S3 Bucket**: Configuration backups (optional)
- **Parameter Store**: Encrypted credentials (3 parameters)

### Monitoring
- **CloudWatch Log Group**: Asterisk logs
- **CloudWatch Alarms**: 5+ alarms (CPU, memory, SIP, calls)
- **CloudWatch Dashboard**: Real-time metrics visualization
- **SNS Topic**: Email notifications

### Security
- **IAM Role**: EC2 instance role with least privilege
- **IAM Policy**: CloudWatch, S3, SSM, EC2 permissions
- **Instance Profile**: Attached to EC2

### Estimated Costs

**Development:**
- EC2 t3.small: $15/month
- Elastic IP: $3.60/month
- Storage: $3/month
- **Total: ~$22/month**

**Production:**
- EC2 t3.medium: $30/month
- Elastic IP: $3.60/month
- Storage/Monitoring: $12/month
- **Total: ~$46/month**

**High Availability:**
- Add: $33-40/month (standby instance)
- **Total: ~$80/month**

## Testing & Validation

### Automated Tests

Located in `tests/test_sip_connectivity.py`:

1. **Infrastructure Tests**
   - EC2 instance running
   - Elastic IP associated
   - Security Groups configured
   - S3 buckets exist
   - Parameter Store credentials

2. **Connectivity Tests**
   - SIP TCP port reachable
   - RTP port range accessible
   - CloudWatch logs streaming

3. **Integration Tests** (requires SSH)
   - Asterisk service healthy
   - PJSIP endpoint configured
   - ElevenLabs registration status

### Manual Testing

```bash
# Quick health check
sudo asterisk -rx "pjsip show endpoints"
sudo asterisk -rx "core show channels"

# Test outbound call
sudo asterisk -rx "channel originate PJSIP/NUMBER@elevenlabs application Echo"

# Monitor call quality
sudo asterisk -rx "pjsip show channelstats"
```

## Security Best Practices

✅ **Implemented:**
- Minimal Security Group rules (only required ports)
- Credentials encrypted in Parameter Store
- Fail2Ban for brute-force protection
- IAM roles with least privilege
- S3 bucket access restrictions
- VPC isolation

🔧 **Recommended for Production:**
- Enable TLS for SIP signaling
- VPN access instead of public SSH
- IP whitelisting for known endpoints
- Regular security patches via automation
- AWS Config for compliance monitoring
- CloudTrail for audit logging

## Known Limitations

1. **Single Region**: No multi-region failover (use Route 53 health checks)
2. **No Load Balancing**: Single instance (use DNS-based load distribution)
3. **Manual Scaling**: No auto-scaling (monitor and resize manually)
4. **TCP Only by Default**: TLS requires additional configuration
5. **Amazon Linux 2**: AL2023 has compilation issues (use AL2)

## Troubleshooting Quick Reference

| Issue | Diagnostic | Solution |
|-------|-----------|----------|
| One-way audio | `tcpdump udp portrange 10000-20000` | Check Security Group RTP rules |
| SIP registration fails | `asterisk -rx "pjsip set logger on"` | Verify credentials in Parameter Store |
| TCP transport not working | `netstat -tulnp \| grep 5060` | Reboot instance (not just Asterisk) |
| High CPU usage | `top` + fail2ban status | Enable Fail2Ban, block attackers |
| No CloudWatch logs | Check agent status | Restart amazon-cloudwatch-agent |

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed resolution steps.

## Maintenance Procedures

### Daily
- Monitor CloudWatch alarms
- Check SIP registration status
- Review error logs

### Weekly
- Verify call quality metrics
- Check disk space usage
- Review Fail2Ban ban list

### Monthly
- Update system packages
- Review and optimize dialplan
- Analyze cost and usage
- Test backup restoration

### Quarterly
- Rotate SIP credentials
- Review Security Group rules
- Update Asterisk version
- Conduct failover testing (HA)

## Integration with Existing Systems

### Integration with PrintCast Agent

The existing `/workspace/printcast-agent/` can be integrated:

```bash
# Copy PrintCast dialplan to Asterisk
scp printcast-agent/config/asterisk/extensions.conf \
  ec2-user@$ELASTIC_IP:/etc/asterisk/extensions_printcast.conf

# Include in main dialplan
echo "#include extensions_printcast.conf" | \
  ssh ec2-user@$ELASTIC_IP "sudo tee -a /etc/asterisk/extensions.conf"

# Reload dialplan
ssh ec2-user@$ELASTIC_IP "sudo asterisk -rx 'dialplan reload'"
```

### API Integration

Asterisk supports REST API via ARI (Asterisk REST Interface):

```bash
# Enable ARI in ari.conf
[general]
enabled = yes
pretty = yes

[hello]
type = user
read_only = no
password = secure_password
```

Access via: `http://ELASTIC_IP:8088/ari/`

## Roadmap & Future Enhancements

- [ ] AWS CDK alternative to Terraform
- [ ] Auto-scaling based on call volume
- [ ] Multi-region deployment with Route 53 failover
- [ ] WebRTC support for browser-based calls
- [ ] Integration with Amazon Connect
- [ ] Kubernetes deployment option
- [ ] CI/CD pipeline for automated updates
- [ ] Advanced analytics with QuickSight

## Support & Contributing

### Getting Help
1. Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Review Asterisk logs: `/var/log/asterisk/full`
3. Enable debug: `asterisk -rx "pjsip set logger on"`
4. Create issue in project repository

### Contributing
- Follow PEP 257 for Python docstrings
- Use Terraform formatting: `terraform fmt`
- Add tests for new features
- Update documentation

## License

MIT License - See LICENSE file for details

---

**Project Version:** 1.0.0  
**Last Updated:** 2025-10-01  
**Asterisk Version:** 21.x  
**AWS Provider:** 5.x  
**Terraform Version:** >= 1.5.0
