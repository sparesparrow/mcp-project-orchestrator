# AWS SIP Trunk Troubleshooting Guide

Comprehensive guide for diagnosing and resolving common issues with Asterisk SIP trunk deployment on AWS.

## Quick Diagnostic Commands

```bash
# Check Asterisk service status
sudo systemctl status asterisk

# Verify PJSIP endpoints
sudo asterisk -rx "pjsip show endpoints"

# Check transport configuration
sudo asterisk -rx "pjsip show transports"

# View active channels
sudo asterisk -rx "core show channels"

# Enable SIP debug logging
sudo asterisk -rx "pjsip set logger on"

# Check RTP configuration
sudo asterisk -rx "rtp show settings"

# View registration status
sudo asterisk -rx "pjsip show registrations"

# Network connectivity test
sudo tcpdump -i eth0 -n port 5060 or portrange 10000-20000
```

## Issue 1: One-Way Audio or No Audio

### Symptoms
- Call connects but no audio heard
- Audio works in one direction only
- Caller hears nothing, or callee hears nothing

### Root Causes
1. **Security Group blocking RTP ports**
2. **NAT configuration incorrect in pjsip.conf**
3. **Firewall blocking UDP traffic**
4. **Codec mismatch**

### Diagnostic Steps

```bash
# 1. Verify Security Group allows RTP
aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --query 'SecurityGroups[0].IpPermissions[?FromPort>=`10000` && ToPort<=`20000`]'

# 2. Check if RTP packets are flowing
sudo tcpdump -i eth0 -n udp portrange 10000-20000 -c 20

# 3. Verify NAT configuration
sudo asterisk -rx "pjsip show transport transport-tcp"

# 4. Check codec negotiation
sudo asterisk -rx "pjsip show endpoints" | grep -A 5 "elevenlabs"
```

### Solutions

**Solution A: Fix Security Group Rules**
```bash
# Add RTP rule if missing
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol udp \
  --port 10000-20000 \
  --cidr 0.0.0.0/0 \
  --region $AWS_REGION
```

**Solution B: Fix NAT Configuration**

Edit `/etc/asterisk/pjsip.conf`:
```ini
[transport-tcp]
type=transport
protocol=tcp
bind=0.0.0.0:5060
external_media_address=YOUR_ELASTIC_IP      # Must be public IP
external_signaling_address=YOUR_ELASTIC_IP  # Must be public IP
local_net=PRIVATE_IP/16                     # Your VPC CIDR
```

Reload:
```bash
sudo asterisk -rx "pjsip reload"
```

**Solution C: Verify Codec Support**

Edit `/etc/asterisk/pjsip.conf`:
```ini
[elevenlabs]
type=endpoint
allow=!all,ulaw,alaw  # Ensure these codecs are allowed
```

## Issue 2: SIP Registration Failures

### Symptoms
- `pjsip show endpoints` shows "Unavailable"
- Logs show "401 Unauthorized" or "403 Forbidden"
- Cannot place calls

### Root Causes
1. **Incorrect credentials**
2. **E.164 format issue**
3. **Network connectivity problem**
4. **ElevenLabs server unreachable**

### Diagnostic Steps

```bash
# 1. Check endpoint status
sudo asterisk -rx "pjsip show endpoint elevenlabs"

# 2. Test DNS resolution
dig sip.elevenlabs.io

# 3. Test connectivity
telnet sip.elevenlabs.io 5060

# 4. Check logs for auth errors
sudo grep "401\|403\|Authentication" /var/log/asterisk/full | tail -20

# 5. Verify credentials in Parameter Store
aws ssm get-parameter \
  --name "/$PROJECT_NAME/elevenlabs/phone_e164" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text
```

### Solutions

**Solution A: Fix Credentials**

Update Parameter Store:
```bash
aws ssm put-parameter \
  --name "/$PROJECT_NAME/elevenlabs/sip_password" \
  --value "NEW_PASSWORD" \
  --type SecureString \
  --overwrite
```

Update pjsip.conf:
```bash
sudo vim /etc/asterisk/pjsip.conf
# Update password in [elevenlabs-auth] section
sudo asterisk -rx "pjsip reload"
```

**Solution B: Verify E.164 Format**

Ensure phone number is in correct format:
- ✅ Correct: `+12025551234`
- ❌ Wrong: `12025551234`, `+1 (202) 555-1234`

**Solution C: Enable Debug Logging**
```bash
sudo asterisk -rx "pjsip set logger on"
sudo tail -f /var/log/asterisk/full | grep -i "elevenlabs"
```

## Issue 3: TCP Transport Not Enabling

### Symptoms
- TCP port 5060 not listening
- Only UDP transport available
- Cannot connect to ElevenLabs TCP endpoint

### Root Cause
TCP binding requires full system reboot, not just Asterisk reload

### Diagnostic Steps

```bash
# Check listening ports
sudo netstat -tulnp | grep 5060

# Expected output:
# tcp  0  0.0.0.0:5060  0.0.0.0:*  LISTEN  asterisk
# udp  0  0.0.0.0:5060  0.0.0.0:*         asterisk
```

### Solution

**Full System Reboot Required**
```bash
# Save any work
sudo sync

# Reboot instance
sudo reboot

# After reboot, verify
sudo netstat -tulnp | grep 5060
```

**Alternative: Force Asterisk Restart**
```bash
sudo systemctl stop asterisk
sleep 5
sudo systemctl start asterisk
sudo netstat -tulnp | grep 5060
```

## Issue 4: High CPU Usage

### Symptoms
- CPU utilization > 80%
- CloudWatch alarm triggered
- Asterisk becomes unresponsive

### Root Causes
1. **SIP attack (brute force)**
2. **Too many concurrent calls**
3. **Codec transcoding overhead**
4. **Resource leak**

### Diagnostic Steps

```bash
# 1. Check CPU usage
top -b -n 1 | head -20

# 2. Check number of active channels
sudo asterisk -rx "core show channels"

# 3. Check for attack patterns
sudo grep "Failed to authenticate" /var/log/asterisk/full | wc -l

# 4. Check Fail2Ban status
sudo fail2ban-client status asterisk

# 5. Memory usage
free -h
```

### Solutions

**Solution A: Enable/Verify Fail2Ban**
```bash
# Check Fail2Ban status
sudo systemctl status fail2ban

# View banned IPs
sudo fail2ban-client status asterisk

# Manually ban IP
sudo fail2ban-client set asterisk banip ATTACKER_IP
```

**Solution B: Optimize Asterisk Configuration**

Reduce unnecessary logging:
```bash
sudo vim /etc/asterisk/logger.conf
```
```ini
[logfiles]
console => notice,warning,error  # Remove verbose,debug
messages => notice,warning,error
full => notice,warning,error     # Remove verbose
```

**Solution C: Limit Concurrent Calls**

Edit `/etc/asterisk/pjsip.conf`:
```ini
[elevenlabs]
type=endpoint
max_audio_streams=10  # Limit concurrent calls
```

**Solution D: Disable Direct Media**
```ini
[elevenlabs]
type=endpoint
direct_media=no  # Force RTP through Asterisk (better for NAT)
```

## Issue 5: RTP Port Exhaustion

### Symptoms
- Calls fail after specific number of concurrent calls
- "No RTP ports available" in logs
- New calls cannot establish audio

### Root Cause
Default RTP port range too small for concurrent call volume

### Solution

Edit `/etc/asterisk/rtp.conf`:
```ini
[general]
rtpstart=10000
rtpend=20000  # Increase from default 10000-10100
```

Update Security Group:
```bash
# Update to match new range
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol udp \
  --port 10000-20000 \
  --cidr 0.0.0.0/0
```

Reload Asterisk:
```bash
sudo systemctl restart asterisk
```

## Issue 6: Elastic IP Not Persisting After Reboot

### Symptoms
- After instance reboot, Elastic IP not associated
- SIP endpoint unreachable
- Public IP changed

### Root Cause
Elastic IP association lost during stop/start cycle

### Solution

**Automatic Re-association Script**

Create `/usr/local/bin/associate-eip.sh`:
```bash
#!/bin/bash
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
AWS_REGION=$(ec2-metadata --availability-zone | cut -d " " -f 2 | sed 's/[a-z]$//')

# Get Elastic IP allocation ID
ALLOCATION_ID=$(aws ec2 describe-addresses \
  --region $AWS_REGION \
  --filters "Name=tag:Project,Values=$PROJECT_NAME" \
  --query 'Addresses[0].AllocationId' \
  --output text)

# Associate EIP
aws ec2 associate-address \
  --instance-id $INSTANCE_ID \
  --allocation-id $ALLOCATION_ID \
  --region $AWS_REGION
```

Add to systemd:
```bash
sudo cat > /etc/systemd/system/associate-eip.service <<EOF
[Unit]
Description=Associate Elastic IP on boot
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/associate-eip.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable associate-eip.service
```

## Issue 7: CloudWatch Logs Not Appearing

### Symptoms
- Log group exists but no streams
- Metrics not visible in CloudWatch
- Alarms not triggering

### Diagnostic Steps

```bash
# 1. Check CloudWatch agent status
sudo systemctl status amazon-cloudwatch-agent

# 2. View agent logs
sudo cat /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log

# 3. Verify IAM permissions
aws iam get-role-policy \
  --role-name $PROJECT_NAME-asterisk-role \
  --policy-name $PROJECT_NAME-asterisk-policy
```

### Solution

**Restart CloudWatch Agent**
```bash
sudo systemctl restart amazon-cloudwatch-agent
sudo systemctl status amazon-cloudwatch-agent
```

**Verify Log Group Permissions**
```bash
# Check if log group exists
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/ec2/$PROJECT_NAME"

# Create if missing
aws logs create-log-group \
  --log-group-name "/aws/ec2/$PROJECT_NAME/asterisk"
```

## Issue 8: Call Quality Issues (Choppy Audio, Dropouts)

### Symptoms
- Audio cuts in and out
- Robotic/choppy voice
- High latency

### Root Causes
1. **Network congestion**
2. **Insufficient bandwidth**
3. **Packet loss**
4. **Jitter**

### Diagnostic Steps

```bash
# 1. Check network statistics
sudo asterisk -rx "pjsip show channelstats"

# 2. Monitor RTP packets
sudo tcpdump -i eth0 -n udp portrange 10000-20000 -vv

# 3. Check system performance
vmstat 1 10
iostat -x 1 10

# 4. Verify codec
sudo asterisk -rx "core show channels verbose"
```

### Solutions

**Solution A: QoS Configuration**

Enable QoS on instance:
```bash
# Set TOS bits for RTP
sudo sysctl -w net.ipv4.ip_default_ttl=64
sudo sysctl -w net.ipv4.tcp_mtu_probing=1
```

**Solution B: Adjust Jitter Buffer**

Edit `/etc/asterisk/pjsip.conf`:
```ini
[elevenlabs]
type=endpoint
use_ptime=yes
allow=!all,ulaw  # Use only ulaw for consistency
```

**Solution C: Increase Instance Size**

If CPU > 60% during calls:
```bash
# Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID

# Change instance type
aws ec2 modify-instance-attribute \
  --instance-id $INSTANCE_ID \
  --instance-type t3.large

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID
```

## Issue 9: Asterisk Won't Start After Reboot

### Symptoms
- `systemctl status asterisk` shows failed
- No Asterisk processes running
- Cannot access Asterisk CLI

### Diagnostic Steps

```bash
# 1. Check service status
sudo systemctl status asterisk -l

# 2. View Asterisk logs
sudo cat /var/log/asterisk/full | tail -50

# 3. Check for configuration errors
sudo asterisk -cvvvvv
# Look for error messages during startup

# 4. Verify file permissions
ls -la /etc/asterisk/
ls -la /var/lib/asterisk/
```

### Solutions

**Solution A: Fix Configuration Errors**
```bash
# Test configuration
sudo asterisk -cvvvvv

# If syntax errors, fix them
sudo vim /etc/asterisk/pjsip.conf

# Restart
sudo systemctl restart asterisk
```

**Solution B: Fix Permissions**
```bash
sudo chown -R asterisk:asterisk /etc/asterisk
sudo chown -R asterisk:asterisk /var/{lib,log,spool}/asterisk
sudo systemctl restart asterisk
```

**Solution C: Rebuild Asterisk**
```bash
# If all else fails, reinstall
cd /usr/src/asterisk-*
sudo make uninstall
sudo make install
sudo systemctl restart asterisk
```

## Emergency Procedures

### Complete System Reset

```bash
# 1. Stop Asterisk
sudo systemctl stop asterisk

# 2. Backup current configuration
sudo tar -czf /tmp/asterisk-backup-$(date +%Y%m%d).tar.gz /etc/asterisk/

# 3. Restore known-good configuration
sudo tar -xzf /path/to/backup.tar.gz -C /

# 4. Start Asterisk
sudo systemctl start asterisk
```

### Quick Health Check Script

Save as `/usr/local/bin/asterisk-health.sh`:
```bash
#!/bin/bash

echo "=== Asterisk Health Check ==="
echo "Service Status:"
systemctl is-active asterisk

echo -e "\nEndpoint Status:"
asterisk -rx "pjsip show endpoints" | grep elevenlabs

echo -e "\nActive Channels:"
asterisk -rx "core show channels" | tail -1

echo -e "\nCPU/Memory:"
top -bn1 | grep "Cpu\|asterisk" | head -2

echo -e "\nRTP Ports:"
netstat -an | grep -E ":(1[0-9]{4}|20000)" | wc -l

echo -e "\nRecent Errors:"
tail -20 /var/log/asterisk/full | grep ERROR
```

## Getting Help

### Collect Diagnostic Information

Before seeking help, collect:
```bash
#!/bin/bash
# diagnostic-report.sh

REPORT_DIR="/tmp/asterisk-diagnostics-$(date +%Y%m%d-%H%M%S)"
mkdir -p $REPORT_DIR

# System info
uname -a > $REPORT_DIR/system-info.txt
free -h >> $REPORT_DIR/system-info.txt
df -h >> $REPORT_DIR/system-info.txt

# Asterisk status
sudo asterisk -rx "core show version" > $REPORT_DIR/asterisk-version.txt
sudo asterisk -rx "pjsip show endpoints" > $REPORT_DIR/endpoints.txt
sudo asterisk -rx "pjsip show transports" > $REPORT_DIR/transports.txt

# Logs
sudo tail -1000 /var/log/asterisk/full > $REPORT_DIR/asterisk-full.log
sudo tail -1000 /var/log/asterisk/messages > $REPORT_DIR/asterisk-messages.log

# Configuration
sudo cp /etc/asterisk/pjsip.conf $REPORT_DIR/
sudo cp /etc/asterisk/extensions.conf $REPORT_DIR/
sudo cp /etc/asterisk/rtp.conf $REPORT_DIR/

# Network
sudo netstat -tulnp | grep asterisk > $REPORT_DIR/network.txt
ip addr > $REPORT_DIR/ip-config.txt

# Create archive
tar -czf $REPORT_DIR.tar.gz $REPORT_DIR
echo "Diagnostic report created: $REPORT_DIR.tar.gz"
```

### Community Resources

- **Asterisk Community Forum**: https://community.asterisk.org/
- **ElevenLabs Support**: https://help.elevenlabs.io/
- **AWS Support**: https://aws.amazon.com/premiumsupport/
- **Project Issues**: File issue in project repository

## Performance Tuning

### Optimize for High Call Volume

```ini
# /etc/asterisk/pjsip.conf
[global]
max_forwards=20  # Reduce from default 70
timer_t1=500     # SIP timer (default)
timer_b=32000    # Transaction timeout

[transport-tcp]
type=transport
async_operations=10  # Increase for high concurrency
```

### Kernel Tuning

```bash
# /etc/sysctl.conf
net.ipv4.ip_local_port_range = 10000 65535
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216

# Apply
sudo sysctl -p
```

---

**Last Updated**: 2025-10-01
**Version**: 1.0.0
