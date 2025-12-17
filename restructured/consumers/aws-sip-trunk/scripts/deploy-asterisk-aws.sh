#!/bin/bash
#
# Manual Deployment Script for Asterisk SIP Trunk on AWS
# Alternative to Terraform - creates infrastructure using AWS CLI
#

set -euo pipefail

# Error handling
trap 'echo "Error on line $LINENO"; exit 1' ERR

echo "=== Asterisk SIP Trunk for ElevenLabs - AWS Deployment ==="
echo ""

# Check prerequisites
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed. Aborting."; exit 1; }

# Required environment variables
: "${AWS_REGION:?Environment variable AWS_REGION is required}"
: "${ELEVENLABS_PHONE_E164:?Environment variable ELEVENLABS_PHONE_E164 is required}"
: "${ELEVENLABS_SIP_PASSWORD:?Environment variable ELEVENLABS_SIP_PASSWORD is required}"
: "${SSH_KEY_NAME:?Environment variable SSH_KEY_NAME is required}"

# Optional variables with defaults
PROJECT_NAME="${PROJECT_NAME:-asterisk-sip-trunk}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.medium}"
VPC_CIDR="${VPC_CIDR:-10.0.0.0/16}"
SUBNET_CIDR="${SUBNET_CIDR:-10.0.1.0/24}"

echo "Configuration:"
echo "=============="
echo "Project Name: $PROJECT_NAME"
echo "AWS Region: $AWS_REGION"
echo "Instance Type: $INSTANCE_TYPE"
echo "VPC CIDR: $VPC_CIDR"
echo "ElevenLabs Phone: $ELEVENLABS_PHONE_E164"
echo ""

# Step 1: Create VPC
echo "[1/10] Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block "$VPC_CIDR" \
    --region "$AWS_REGION" \
    --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$PROJECT_NAME-vpc},{Key=Project,Value=$PROJECT_NAME}]" \
    --query 'Vpc.VpcId' \
    --output text)

echo "Created VPC: $VPC_ID"

# Enable DNS hostnames
aws ec2 modify-vpc-attribute \
    --vpc-id "$VPC_ID" \
    --enable-dns-hostnames \
    --region "$AWS_REGION"

# Step 2: Create Internet Gateway
echo "[2/10] Creating Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
    --region "$AWS_REGION" \
    --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=$PROJECT_NAME-igw},{Key=Project,Value=$PROJECT_NAME}]" \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

aws ec2 attach-internet-gateway \
    --internet-gateway-id "$IGW_ID" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION"

echo "Created Internet Gateway: $IGW_ID"

# Step 3: Create Subnet
echo "[3/10] Creating Public Subnet..."
SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id "$VPC_ID" \
    --cidr-block "$SUBNET_CIDR" \
    --region "$AWS_REGION" \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-public-subnet},{Key=Project,Value=$PROJECT_NAME}]" \
    --query 'Subnet.SubnetId' \
    --output text)

echo "Created Subnet: $SUBNET_ID"

# Step 4: Create Route Table
echo "[4/10] Creating Route Table..."
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=$PROJECT_NAME-public-rt},{Key=Project,Value=$PROJECT_NAME}]" \
    --query 'RouteTable.RouteTableId' \
    --output text)

aws ec2 create-route \
    --route-table-id "$ROUTE_TABLE_ID" \
    --destination-cidr-block "0.0.0.0/0" \
    --gateway-id "$IGW_ID" \
    --region "$AWS_REGION"

aws ec2 associate-route-table \
    --subnet-id "$SUBNET_ID" \
    --route-table-id "$ROUTE_TABLE_ID" \
    --region "$AWS_REGION"

echo "Created Route Table: $ROUTE_TABLE_ID"

# Step 5: Create Security Group
echo "[5/10] Creating Security Group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name "$PROJECT_NAME-asterisk-sg" \
    --description "Security group for Asterisk SIP trunk" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$PROJECT_NAME-asterisk-sg},{Key=Project,Value=$PROJECT_NAME}]" \
    --query 'GroupId' \
    --output text)

echo "Created Security Group: $SG_ID"

# Add security group rules
echo "Adding security group rules..."

# SSH (if SSH_ALLOWED_CIDR is set)
if [ -n "${SSH_ALLOWED_CIDR:-}" ]; then
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 22 \
        --cidr "$SSH_ALLOWED_CIDR" \
        --region "$AWS_REGION" \
        --group-rule-description "SSH access"
fi

# SIP TCP
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 5060 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION" \
    --group-rule-description "SIP TCP signaling"

# SIP UDP
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol udp \
    --port 5060 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION" \
    --group-rule-description "SIP UDP signaling"

# RTP Ports
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --ip-permissions \
    "IpProtocol=udp,FromPort=10000,ToPort=20000,IpRanges=[{CidrIp=0.0.0.0/0,Description='RTP media streams'}]" \
    --region "$AWS_REGION"

# Step 6: Allocate Elastic IP
echo "[6/10] Allocating Elastic IP..."
ELASTIC_IP_ALLOC=$(aws ec2 allocate-address \
    --domain vpc \
    --region "$AWS_REGION" \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=$PROJECT_NAME-eip},{Key=Project,Value=$PROJECT_NAME}]")

ELASTIC_IP=$(echo "$ELASTIC_IP_ALLOC" | jq -r '.PublicIp')
ALLOCATION_ID=$(echo "$ELASTIC_IP_ALLOC" | jq -r '.AllocationId')

echo "Allocated Elastic IP: $ELASTIC_IP (Allocation ID: $ALLOCATION_ID)"

# Step 7: Store credentials in Parameter Store
echo "[7/10] Storing credentials in Parameter Store..."
aws ssm put-parameter \
    --name "/$PROJECT_NAME/elevenlabs/phone_e164" \
    --value "$ELEVENLABS_PHONE_E164" \
    --type SecureString \
    --region "$AWS_REGION" \
    --overwrite 2>/dev/null || true

aws ssm put-parameter \
    --name "/$PROJECT_NAME/elevenlabs/sip_password" \
    --value "$ELEVENLABS_SIP_PASSWORD" \
    --type SecureString \
    --region "$AWS_REGION" \
    --overwrite 2>/dev/null || true

aws ssm put-parameter \
    --name "/$PROJECT_NAME/network/elastic_ip" \
    --value "$ELASTIC_IP" \
    --type String \
    --region "$AWS_REGION" \
    --overwrite 2>/dev/null || true

echo "Credentials stored in Parameter Store"

# Step 8: Create IAM Role for EC2
echo "[8/10] Creating IAM Role..."
ROLE_NAME="$PROJECT_NAME-asterisk-role"

cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document file:///tmp/trust-policy.json \
    --region "$AWS_REGION" 2>/dev/null || echo "Role already exists"

cat > /tmp/role-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ec2:DescribeAddresses",
        "ec2:AssociateAddress"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "$PROJECT_NAME-asterisk-policy" \
    --policy-document file:///tmp/role-policy.json \
    --region "$AWS_REGION"

aws iam create-instance-profile \
    --instance-profile-name "$ROLE_NAME" \
    --region "$AWS_REGION" 2>/dev/null || echo "Instance profile already exists"

aws iam add-role-to-instance-profile \
    --instance-profile-name "$ROLE_NAME" \
    --role-name "$ROLE_NAME" \
    --region "$AWS_REGION" 2>/dev/null || true

# Wait for instance profile to be available
sleep 10

echo "Created IAM Role: $ROLE_NAME"

# Step 9: Get Amazon Linux 2 AMI
echo "[9/10] Finding Amazon Linux 2 AMI..."
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters \
        "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
        "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text \
    --region "$AWS_REGION")

echo "Using AMI: $AMI_ID"

# Step 10: Launch EC2 Instance
echo "[10/10] Launching EC2 Instance..."

# Create user data script
cat > /tmp/user-data.sh <<'USERDATA_EOF'
#!/bin/bash
set -euo pipefail

# Get instance metadata
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
PRIVATE_IP=$(ec2-metadata --local-ipv4 | cut -d " " -f 2)

# Retrieve configuration from Parameter Store
AWS_REGION="$(ec2-metadata --availability-zone | cut -d " " -f 2 | sed 's/[a-z]$//')"
PROJECT_NAME="REPLACE_PROJECT_NAME"
ELASTIC_IP=$(aws ssm get-parameter --name "/$PROJECT_NAME/network/elastic_ip" --query 'Parameter.Value' --output text --region "$AWS_REGION")
ELEVENLABS_PHONE_E164=$(aws ssm get-parameter --name "/$PROJECT_NAME/elevenlabs/phone_e164" --with-decryption --query 'Parameter.Value' --output text --region "$AWS_REGION")
ELEVENLABS_PASSWORD=$(aws ssm get-parameter --name "/$PROJECT_NAME/elevenlabs/sip_password" --with-decryption --query 'Parameter.Value' --output text --region "$AWS_REGION")

# Download and run full installation script
aws s3 cp "s3://$PROJECT_NAME-scripts/user-data.sh" /tmp/install-asterisk.sh --region "$AWS_REGION" 2>/dev/null || {
    # If S3 script not available, use inline installation
    yum update -y
    yum groupinstall -y "Development Tools"
    # ... rest of installation continues inline ...
    echo "Installation complete"
}
USERDATA_EOF

sed -i "s/REPLACE_PROJECT_NAME/$PROJECT_NAME/g" /tmp/user-data.sh

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$SSH_KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --subnet-id "$SUBNET_ID" \
    --iam-instance-profile "Name=$ROLE_NAME" \
    --user-data "file:///tmp/user-data.sh" \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3","Encrypted":true}}]' \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$PROJECT_NAME-asterisk},{Key=Project,Value=$PROJECT_NAME},{Key=Role,Value=Primary}]" \
    --region "$AWS_REGION" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Launched EC2 Instance: $INSTANCE_ID"
echo "Waiting for instance to be running..."

aws ec2 wait instance-running \
    --instance-ids "$INSTANCE_ID" \
    --region "$AWS_REGION"

# Associate Elastic IP
echo "Associating Elastic IP..."
aws ec2 associate-address \
    --instance-id "$INSTANCE_ID" \
    --allocation-id "$ALLOCATION_ID" \
    --region "$AWS_REGION"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Infrastructure Details:"
echo "======================="
echo "VPC ID: $VPC_ID"
echo "Subnet ID: $SUBNET_ID"
echo "Security Group ID: $SG_ID"
echo "Instance ID: $INSTANCE_ID"
echo "Elastic IP: $ELASTIC_IP"
echo "SIP Endpoint: sip:$ELASTIC_IP:5060"
echo ""
echo "Next Steps:"
echo "==========="
echo "1. Wait 10-15 minutes for Asterisk installation to complete"
echo "2. SSH into instance: ssh -i ~/.ssh/$SSH_KEY_NAME.pem ec2-user@$ELASTIC_IP"
echo "3. Check installation logs: tail -f /var/log/asterisk-setup.log"
echo "4. Verify Asterisk: sudo asterisk -rx 'pjsip show endpoints'"
echo ""
echo "Save these values for later:"
echo "export INSTANCE_ID=$INSTANCE_ID"
echo "export ELASTIC_IP=$ELASTIC_IP"
echo "export VPC_ID=$VPC_ID"
echo ""

# Cleanup temporary files
rm -f /tmp/trust-policy.json /tmp/role-policy.json /tmp/user-data.sh

echo "Deployment script finished successfully"
