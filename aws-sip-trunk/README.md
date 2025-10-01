# AWS SIP Trunk Deployment for ElevenLabs

Complete infrastructure-as-code solution for deploying Asterisk-based SIP trunk on AWS EC2 with ElevenLabs integration.

## Architecture Overview

This deployment creates a production-ready SIP trunk infrastructure using:

- **Amazon EC2**: t3.medium instance running Asterisk 21 with PJSIP
- **Elastic IP**: Static public IP for consistent SIP endpoint addressing
- **VPC & Security Groups**: Network isolation with controlled SIP/RTP traffic
- **Route 53**: DNS configuration for SIP SRV records (optional)
- **CloudWatch**: Monitoring and alerting for call metrics
- **Systems Manager Parameter Store**: Secure credential storage
- **S3**: Call recordings and configuration backup storage

## Quick Start

### Prerequisites

1. AWS CLI configured with credentials
2. Terraform >= 1.5.0 or AWS CDK >= 2.0
3. ElevenLabs account with SIP trunk credentials

### Environment Setup

```bash
# Export required variables
export AWS_REGION="us-east-1"
export ELEVENLABS_PHONE_E164="+12025551234"
export ELEVENLABS_SIP_PASSWORD="your-sip-password"
export PROJECT_NAME="asterisk-sip-trunk"

# Run deployment
cd /workspace/aws-sip-trunk/terraform
terraform init
terraform plan
terraform apply
```

### Manual Deployment (Alternative)

```bash
# Launch EC2 instance and run bootstrap script
cd /workspace/aws-sip-trunk/scripts
./deploy-asterisk-aws.sh
```

## Project Structure

```
aws-sip-trunk/
├── terraform/
│   ├── main.tf              # Main infrastructure
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Export values
│   ├── ec2.tf              # EC2 instance configuration
│   ├── networking.tf       # VPC, Security Groups
│   ├── monitoring.tf       # CloudWatch setup
│   └── storage.tf          # S3 and Parameter Store
├── scripts/
│   ├── deploy-asterisk-aws.sh    # Bootstrap script
│   ├── configure-pjsip.sh        # PJSIP configuration
│   └── monitoring-setup.sh       # CloudWatch agent
├── config/
│   ├── pjsip.conf.j2       # PJSIP template
│   ├── extensions.conf.j2  # Dialplan template
│   ├── rtp.conf            # RTP configuration
│   └── cloudwatch-config.json
├── tests/
│   ├── test_sip_connectivity.py
│   └── test_rtp_media.py
├── docs/
│   ├── DEPLOYMENT.md       # Detailed deployment guide
│   ├── TROUBLESHOOTING.md  # Common issues
│   └── ARCHITECTURE.md     # Design decisions
└── README.md
```

## Known Issues

### EC2 NAT/SIP Issues
- **Problem**: Asterisk advertises private IP in SDP
- **Solution**: Configure `external_media_address` and `external_signaling_address` in pjsip.conf
- **Diagnostic**: `asterisk -rx "pjsip set logger on"`

### TCP Transport Not Enabling
- **Problem**: TCP transport doesn't activate after reload
- **Solution**: Full system reboot required, not just Asterisk reload
- **Diagnostic**: `netstat -tulnp | grep 5060`

### RTP Port Exhaustion
- **Problem**: High call volume exceeds RTP port range
- **Solution**: Expand range to 10000-20000 and update Security Group
- **Diagnostic**: `asterisk -rx "rtp show settings"`

### Security Group Misconfiguration
- **Problem**: SIP registers but no audio (one-way calls)
- **Solution**: Ensure UDP 10000-20000 (RTP) is open bidirectionally
- **Diagnostic**: `tcpdump -i eth0 udp portrange 10000-20000`

## Monitoring

### CloudWatch Metrics
- `SIP/RegistrationStatus`: Trunk registration health
- `SIP/ActiveCalls`: Current call count
- `RTP/PacketLoss`: Media quality
- `System/CPUUtilization`: Instance health

### Alarms
- SIP trunk offline > 5 minutes
- Call failure rate > 10%
- RTP packet loss > 5%
- CPU utilization > 80%

## Cost Estimation

- EC2 t3.medium: ~$30/month
- Elastic IP: $3.60/month (while instance is running)
- CloudWatch: ~$5/month (standard metrics)
- S3 storage: ~$1/month (100GB call recordings)
- Data transfer: Variable based on call volume

**Total**: ~$40-60/month for production deployment

## Security Best Practices

1. **Minimal Security Group Rules**: Only open required ports (5060, 10000-20000)
2. **Parameter Store Encryption**: All credentials encrypted with KMS
3. **Fail2Ban**: Automatic IP blocking for brute-force attacks
4. **TLS Transport**: Use TLS for SIP signaling (recommended)
5. **IAM Roles**: EC2 instance role for CloudWatch/S3 access only

## Support

For issues or questions:
- Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Review Asterisk logs: `tail -f /var/log/asterisk/full`
- Enable debug: `asterisk -rx "pjsip set logger on"`

## License

MIT License - See LICENSE file for details
