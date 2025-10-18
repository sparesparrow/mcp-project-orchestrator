# AWS SIP Trunk Quick Start Guide

Get your Asterisk SIP trunk running on AWS in under 30 minutes.

## Prerequisites Checklist

- [ ] AWS account with admin access
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Terraform >= 1.5.0 installed (or Bash for manual deployment)
- [ ] SSH key pair created in AWS console
- [ ] ElevenLabs account with SIP trunk credentials
- [ ] Phone number from ElevenLabs in E.164 format

## 5-Minute Setup (Terraform)

### Step 1: Configure Environment (2 min)

```bash
# Navigate to project
cd /workspace/aws-sip-trunk/terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

Required values in `terraform.tfvars`:
```hcl
aws_region                  = "us-east-1"
ssh_key_name                = "my-aws-key"
elevenlabs_phone_e164       = "+12025551234"
elevenlabs_sip_password     = "your-password-here"
alarm_email                 = "you@example.com"
```

### Step 2: Deploy Infrastructure (1 min)

```bash
# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Deploy (type 'yes' when prompted)
terraform apply
```

### Step 3: Wait for Asterisk Installation (15-20 min)

Terraform will complete in 2-3 minutes, but Asterisk compilation takes 15-20 minutes.

```bash
# Get your instance details
export ELASTIC_IP=$(terraform output -raw asterisk_public_ip)
export INSTANCE_ID=$(terraform output -raw asterisk_instance_id)
export SSH_KEY="your-key-name"

# Monitor installation progress
ssh -i ~/.ssh/$SSH_KEY.pem ec2-user@$ELASTIC_IP \
  "tail -f /var/log/asterisk-setup.log"
```

Look for:
```
=== Asterisk SIP Trunk Installation Complete ===
```

### Step 4: Verify Installation (2 min)

```bash
# SSH into instance
ssh -i ~/.ssh/$SSH_KEY.pem ec2-user@$ELASTIC_IP

# Check Asterisk status
sudo systemctl status asterisk

# Verify PJSIP endpoint
sudo asterisk -rx "pjsip show endpoints"
```

Expected output:
```
Endpoint:  elevenlabs                                          Unavailable   0 of inf
```

"Unavailable" is normal until you configure ElevenLabs side.

## Configure ElevenLabs (5 min)

### Step 1: Login to ElevenLabs Dashboard

1. Go to https://elevenlabs.io/app/conversational-ai
2. Navigate to your agent settings
3. Go to "Phone Numbers" or "SIP Trunking" section

### Step 2: Add SIP Trunk

Configure these settings:

```
SIP Server:     YOUR_ELASTIC_IP:5060
Transport:      TCP
Username:       +12025551234 (your E.164 number)
Password:       (your SIP password)
Codecs:         ulaw, alaw
```

### Step 3: Test Connectivity

Back on your Asterisk server:

```bash
# Check if endpoint is now available
sudo asterisk -rx "pjsip show endpoints"
```

Should show:
```
Endpoint:  elevenlabs                                          Available     0 of inf
```

## Test Your First Call (5 min)

### Inbound Test (from ElevenLabs to Asterisk)

1. In ElevenLabs dashboard, initiate a test call to your Asterisk number
2. Monitor on Asterisk:

```bash
sudo asterisk -rx "core show channels"
```

### Outbound Test (from Asterisk to ElevenLabs)

```bash
# Replace AGENT_NUMBER with your ElevenLabs agent number
sudo asterisk -rx "channel originate PJSIP/AGENT_NUMBER@elevenlabs application Playback hello-world"
```

## Troubleshooting Quick Fixes

### Issue: "One-way audio" or "No audio"

```bash
# Check Security Group allows RTP
aws ec2 describe-security-groups --group-ids $SG_ID | grep 10000

# If missing, add RTP rule
terraform apply -auto-approve
```

### Issue: "Endpoint shows Unavailable"

```bash
# Enable debug logging
sudo asterisk -rx "pjsip set logger on"

# Watch logs for authentication errors
sudo tail -f /var/log/asterisk/full | grep elevenlabs
```

Common causes:
- Wrong password → Update in terraform.tfvars and `terraform apply`
- E.164 format wrong → Must start with `+` (e.g., `+12025551234`)
- ElevenLabs not configured → Complete ElevenLabs setup above

### Issue: "Cannot SSH to instance"

```bash
# Check if Security Group allows SSH from your IP
MY_IP=$(curl -s ifconfig.me)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr $MY_IP/32
```

## Next Steps

### Enable Call Recording

```bash
# SSH to instance
ssh -i ~/.ssh/$SSH_KEY.pem ec2-user@$ELASTIC_IP

# Edit dialplan (already configured if terraform enable_call_recordings=true)
sudo vim /etc/asterisk/extensions.conf

# Reload dialplan
sudo asterisk -rx "dialplan reload"
```

### View CloudWatch Dashboard

```bash
# Get dashboard URL
terraform output cloudwatch_dashboard_url

# Open in browser
```

### Monitor Call Quality

```bash
# Real-time channel statistics
sudo asterisk -rx "pjsip show channelstats"

# View active calls
sudo asterisk -rx "core show channels verbose"
```

### Check Recordings (if enabled)

```bash
# Local recordings
ls -lh /var/spool/asterisk/recordings/

# S3 recordings
aws s3 ls s3://$(terraform output -raw recordings_bucket)/
```

## Production Checklist

Before going to production:

- [ ] Enable TLS transport (`enable_tls = true` in terraform.tfvars)
- [ ] Configure DNS with Route 53 (optional but recommended)
- [ ] Set up CloudWatch alarms (automatic if `alarm_email` set)
- [ ] Enable high availability (`enable_high_availability = true`)
- [ ] Review Security Group rules (restrict SSH to your IP)
- [ ] Test failover procedures
- [ ] Document your dialplan customizations
- [ ] Set up backup procedures (automatic if `backup_enabled = true`)

## Cost Estimate

**Development/Testing:**
- EC2 t3.small: ~$15/month
- Elastic IP: $3.60/month
- CloudWatch/S3: ~$5/month
- **Total: ~$25/month**

**Production:**
- EC2 t3.medium: ~$30/month
- Elastic IP: $3.60/month
- CloudWatch/S3: ~$10/month
- **Total: ~$45/month**

## Getting Help

### View Logs
```bash
# Full Asterisk log
sudo tail -f /var/log/asterisk/full

# Error messages only
sudo grep ERROR /var/log/asterisk/full | tail -20

# Installation log
tail -f /var/log/asterisk-setup.log
```

### Useful Commands
```bash
# Restart Asterisk
sudo systemctl restart asterisk

# Reload specific module
sudo asterisk -rx "module reload res_pjsip.so"

# Show SIP peers
sudo asterisk -rx "pjsip show endpoints"

# Show transports
sudo asterisk -rx "pjsip show transports"

# Enable verbose debugging
sudo asterisk -rx "core set verbose 5"
sudo asterisk -rx "pjsip set logger on"
```

### Documentation
- Full deployment guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Troubleshooting: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Asterisk docs: https://docs.asterisk.org/
- ElevenLabs SIP: https://elevenlabs.io/docs/agents-platform/phone-numbers/sip-trunking

## Cleanup (When Done Testing)

```bash
# Destroy all resources
cd /workspace/aws-sip-trunk/terraform
terraform destroy

# Type 'yes' when prompted
# This will delete: EC2, VPC, S3 buckets (if empty), all configurations
```

**Warning:** This is irreversible. Backup any recordings first!

---

**Questions?** Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) or create an issue in the project repository.
