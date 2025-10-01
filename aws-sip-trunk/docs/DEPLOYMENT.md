# AWS SIP Trunk Deployment Guide

Complete step-by-step guide for deploying Asterisk-based SIP trunk infrastructure on AWS for ElevenLabs integration.

## Prerequisites

### Required Tools
- AWS CLI v2.x configured with credentials
- Terraform >= 1.5.0 (for IaC deployment) OR Bash (for manual deployment)
- SSH client for server access
- jq (for JSON parsing in scripts)

### AWS Account Requirements
- Active AWS account with administrative access
- EC2, VPC, S3, CloudWatch, Systems Manager permissions
- Available Elastic IP quota (at least 1)
- SSH key pair created in target region

### ElevenLabs Requirements
- ElevenLabs account with SIP trunk capability
- Phone number registered in E.164 format
- SIP trunk credentials (username/password)

## Deployment Method 1: Terraform (Recommended)

### Step 1: Prepare Environment

```bash
# Clone or navigate to project directory
cd /workspace/aws-sip-trunk

# Export required variables
export AWS_REGION="us-east-1"
export TF_VAR_ssh_key_name="your-ssh-key-name"
export TF_VAR_elevenlabs_phone_e164="+12025551234"
export TF_VAR_elevenlabs_sip_password="your-sip-password"
export TF_VAR_alarm_email="your-email@example.com"  # Optional

# Optional: Customize deployment
export TF_VAR_instance_type="t3.medium"
export TF_VAR_environment="prod"
export TF_VAR_enable_high_availability="false"
```

### Step 2: Initialize Terraform

```bash
cd terraform
terraform init
```

### Step 3: Review Planned Changes

```bash
terraform plan
```

Review the output to understand what resources will be created:
- VPC with public subnet
- EC2 instance (t3.medium by default)
- Elastic IP
- Security Groups with SIP/RTP rules
- S3 buckets for recordings and backups
- CloudWatch monitoring and alarms
- Systems Manager parameters for credentials

### Step 4: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. Deployment takes approximately 15-20 minutes:
- 2-3 minutes for infrastructure provisioning
- 12-15 minutes for Asterisk compilation and configuration

### Step 5: Verify Deployment

```bash
# Get deployment outputs
terraform output

# Save important values
INSTANCE_ID=$(terraform output -raw asterisk_instance_id)
ELASTIC_IP=$(terraform output -raw asterisk_public_ip)
SIP_ENDPOINT=$(terraform output -raw sip_endpoint)

echo "SIP Endpoint: $SIP_ENDPOINT"
```

### Step 6: Test SIP Connectivity

```bash
# SSH into instance
SSH_COMMAND=$(terraform output -raw ssh_command)
eval $SSH_COMMAND

# Once logged in, check Asterisk status
sudo asterisk -rx "core show version"
sudo asterisk -rx "pjsip show endpoints"
sudo asterisk -rx "pjsip show transports"

# Enable detailed logging for troubleshooting
sudo asterisk -rx "pjsip set logger on"

# Check logs
sudo tail -f /var/log/asterisk/full
```

### Step 7: Configure ElevenLabs

In your ElevenLabs dashboard:

1. Navigate to SIP Trunk configuration
2. Add new SIP trunk with these settings:
   - **SIP Server**: `sip:YOUR_ELASTIC_IP:5060`
   - **Transport**: TCP
   - **Username**: Your E.164 phone number (e.g., `+12025551234`)
   - **Password**: Your SIP trunk password
   - **Codec**: ulaw, alaw

3. Assign the SIP trunk to your ElevenLabs agent

### Step 8: Test Call Flow

```bash
# From Asterisk CLI, test outbound call to ElevenLabs
sudo asterisk -rx "channel originate PJSIP/YOUR_AGENT_NUMBER@elevenlabs extension s@from-elevenlabs"

# Monitor call progress
sudo asterisk -rx "core show channels"
sudo asterisk -rx "pjsip show channelstats"
```

## Deployment Method 2: Manual Script

Alternative deployment using AWS CLI commands directly.

### Step 1: Set Environment Variables

```bash
export AWS_REGION="us-east-1"
export PROJECT_NAME="asterisk-sip-trunk"
export ELEVENLABS_PHONE_E164="+12025551234"
export ELEVENLABS_SIP_PASSWORD="your-sip-password"
export SSH_KEY_NAME="your-ssh-key-name"
export SSH_ALLOWED_CIDR="YOUR_IP/32"  # Optional, for SSH access
```

### Step 2: Run Deployment Script

```bash
cd /workspace/aws-sip-trunk/scripts
./deploy-asterisk-aws.sh
```

The script will:
1. Create VPC and networking components
2. Configure security groups
3. Allocate Elastic IP
4. Store credentials in Parameter Store
5. Create IAM roles
6. Launch EC2 instance with Asterisk

### Step 3: Monitor Installation

```bash
# Wait for instance to be running
aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text

# SSH and monitor installation logs
ssh -i ~/.ssh/$SSH_KEY_NAME.pem ec2-user@$ELASTIC_IP
tail -f /var/log/asterisk-setup.log
```

Installation is complete when you see:
```
=== Asterisk SIP Trunk Installation Complete ===
```

## Post-Deployment Configuration

### Enable Call Recordings

Edit `/etc/asterisk/extensions.conf` on the server:

```asterisk
[from-elevenlabs]
exten => _X.,1,NoOp(Incoming call from ElevenLabs)
 same => n,Set(CALLFILENAME=rec_${STRFTIME(${EPOCH},,%Y%m%d-%H%M%S)}_${CALLERID(num)})
 same => n,MixMonitor(/var/spool/asterisk/recordings/${CALLFILENAME}.wav)
 same => n,Answer()
 ; ... rest of dialplan
```

Reload configuration:
```bash
sudo asterisk -rx "dialplan reload"
```

### Configure TLS (Optional but Recommended)

Generate self-signed certificate:
```bash
sudo openssl req -new -x509 -days 365 -nodes \
  -out /etc/asterisk/asterisk.pem \
  -keyout /etc/asterisk/asterisk.key
sudo chown asterisk:asterisk /etc/asterisk/asterisk.*
```

Update `/etc/asterisk/pjsip.conf`:
```ini
[transport-tls]
type=transport
protocol=tls
bind=0.0.0.0:5061
cert_file=/etc/asterisk/asterisk.pem
priv_key_file=/etc/asterisk/asterisk.key
external_media_address=YOUR_ELASTIC_IP
external_signaling_address=YOUR_ELASTIC_IP
```

Update Security Group to allow TCP 5061:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5061 \
  --cidr 0.0.0.0/0 \
  --region $AWS_REGION
```

Reload Asterisk:
```bash
sudo systemctl restart asterisk
```

### Configure DNS (Optional)

If using Route 53:

```bash
# Create A record
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "sip.yourdomain.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "YOUR_ELASTIC_IP"}]
      }
    }]
  }'

# Create SRV record
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "_sip._tcp.yourdomain.com",
        "Type": "SRV",
        "TTL": 300,
        "ResourceRecords": [{"Value": "10 50 5060 sip.yourdomain.com"}]
      }
    }]
  }'
```

## Monitoring and Maintenance

### CloudWatch Dashboard

Access your deployment dashboard:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=asterisk-sip-trunk-dashboard
```

Key metrics to monitor:
- **CPU Utilization**: Should be < 30% under normal load
- **Memory Usage**: Should be < 70%
- **SIP Registration Failures**: Should be 0
- **Call Failures**: Should be < 5%
- **RTP Packet Loss**: Should be < 1%

### Log Analysis

View Asterisk logs:
```bash
# Full log
sudo tail -f /var/log/asterisk/full

# Filter for errors
sudo grep ERROR /var/log/asterisk/full | tail -20

# View specific call
sudo grep "Call-ID-HERE" /var/log/asterisk/full
```

CloudWatch Logs Insights queries:
```
# Count errors by type
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by @message
| sort count desc

# Call duration analysis
fields @timestamp, @message
| filter @message like /CDR/
| parse @message "duration=*," as duration
| stats avg(duration), max(duration), min(duration)
```

### Backup Configuration

Manual backup:
```bash
# Create backup archive
sudo tar -czf /tmp/asterisk-config-$(date +%Y%m%d).tar.gz \
  /etc/asterisk/

# Upload to S3
aws s3 cp /tmp/asterisk-config-*.tar.gz \
  s3://$PROJECT_NAME-backups-$ACCOUNT_ID/
```

Automated daily backup (already configured via cron):
```bash
# Check backup cron job
sudo crontab -l
```

### Restore from Backup

```bash
# Download backup
aws s3 cp s3://$PROJECT_NAME-backups-$ACCOUNT_ID/asterisk-config-YYYYMMDD.tar.gz /tmp/

# Extract
sudo tar -xzf /tmp/asterisk-config-YYYYMMDD.tar.gz -C /

# Reload Asterisk
sudo asterisk -rx "core reload"
```

## Scaling and High Availability

### Enable HA Mode

Update Terraform variables:
```bash
export TF_VAR_enable_high_availability="true"
terraform apply
```

This creates:
- Secondary EC2 instance in different AZ
- Secondary Elastic IP
- Automatic failover mechanism

### Manual Failover

```bash
# Disassociate EIP from primary
aws ec2 disassociate-address \
  --association-id $ASSOCIATION_ID

# Associate with standby
aws ec2 associate-address \
  --instance-id $STANDBY_INSTANCE_ID \
  --allocation-id $ALLOCATION_ID
```

### Horizontal Scaling

For high call volumes, deploy multiple Asterisk instances behind load balancer:
1. Create Application Load Balancer (TCP mode)
2. Deploy multiple Asterisk instances
3. Use shared RDS database for CDR
4. Configure SIP registration sharing

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

Common issues:
- One-way audio → Check Security Group RTP rules
- Registration failures → Verify credentials in Parameter Store
- High CPU → Check for SIP attacks, enable Fail2Ban
- No audio → Verify NAT configuration in pjsip.conf

## Cost Optimization

### Production Environment
- Use t3.medium for up to 50 concurrent calls
- Enable detailed CloudWatch monitoring
- Set S3 lifecycle policies for recordings
- Estimated cost: ~$50-60/month

### Development Environment
- Use t3.small for testing
- Disable CloudWatch detailed monitoring
- Shorter S3 retention periods
- Estimated cost: ~$25-30/month

### Cost Reduction Tips
1. Use Reserved Instances for 1-year savings (30-40% discount)
2. Enable S3 Intelligent-Tiering for recordings
3. Use VPC Flow Logs only when troubleshooting
4. Delete old CloudWatch logs regularly

## Security Best Practices

1. **Network Security**
   - Restrict SSH access to specific IP ranges
   - Consider VPN access instead of public SSH
   - Enable VPC Flow Logs for audit

2. **Credential Management**
   - Rotate SIP passwords quarterly
   - Use AWS Secrets Manager for production
   - Enable MFA for AWS console access

3. **SIP Security**
   - Enable Fail2Ban (already configured)
   - Monitor for brute-force attacks
   - Consider IP whitelisting for known endpoints

4. **System Security**
   - Enable automatic security updates
   - Regular AMI updates
   - Enable AWS Config for compliance

## Next Steps

1. **Production Readiness Checklist**
   - [ ] Enable TLS for SIP transport
   - [ ] Configure DNS with Route 53
   - [ ] Set up CloudWatch alarms
   - [ ] Test failover procedures
   - [ ] Document call flows
   - [ ] Create runbook for operations

2. **Integration Testing**
   - [ ] Test inbound calls from ElevenLabs
   - [ ] Test outbound calls to ElevenLabs
   - [ ] Verify call recordings
   - [ ] Test DTMF functionality
   - [ ] Load testing with multiple concurrent calls

3. **Monitoring Setup**
   - [ ] Configure SNS notifications
   - [ ] Set up PagerDuty/OpsGenie integration
   - [ ] Create custom CloudWatch dashboards
   - [ ] Enable AWS Cost Anomaly Detection

## Support and Resources

- **Asterisk Documentation**: https://docs.asterisk.org/
- **ElevenLabs SIP Trunk**: https://elevenlabs.io/docs/agents-platform/phone-numbers/sip-trunking
- **AWS VoIP Best Practices**: https://docs.aws.amazon.com/whitepapers/latest/real-time-communication-on-aws/
- **Project Repository**: /workspace/aws-sip-trunk/
