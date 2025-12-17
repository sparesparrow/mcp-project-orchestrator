# AWS MCP Quick Start Guide

This guide helps you quickly get started with the AWS Model Context Protocol integration.

## What is AWS MCP?

AWS MCP adds AI-powered AWS service access to your MCP Project Orchestrator, enabling:
- 🔧 AWS service management (S3, EC2, Lambda, CloudFormation, IAM)
- 📚 AWS best practices and architectural guidance
- 💰 Cost optimization recommendations
- 🔒 Security and compliance guidance

## Quick Setup (3 Steps)

### 1. Install Dependencies

```bash
# Install with AWS support
pip install -e ".[aws]"

# Or just install boto3
pip install boto3 botocore
```

### 2. Configure AWS Credentials

Choose ONE method:

**Method A: Environment Variables** (Simple)
```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

**Method B: .env File** (Recommended for development)
```bash
cp .env.example .env
# Edit .env and add your credentials
```

**Method C: AWS CLI Profile** (Best for existing AWS CLI users)
```bash
aws configure  # If not already configured
export AWS_PROFILE=default
export AWS_REGION=us-east-1
```

**Method D: IAM Role** (Best for production on AWS)
```bash
# No credentials needed!
# Just set the region
export AWS_REGION=us-east-1
```

### 3. Run Setup Script

```bash
./scripts/setup_aws_mcp.sh
```

This will:
- ✅ Check boto3 installation
- ✅ Create .env file
- ✅ Validate AWS configuration
- ✅ Test AWS MCP integration

## Usage Examples

### Python API

```python
from mcp_project_orchestrator.aws_mcp import AWSMCPIntegration, AWSConfig

# Initialize
aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))

# List S3 buckets
buckets = aws.list_s3_buckets()
for bucket in buckets:
    print(f"Bucket: {bucket['Name']}")

# Get best practices
practices = aws.get_aws_best_practices('s3')
print("Security:", practices['security'])
print("Cost:", practices['cost'])
print("Performance:", practices['performance'])

# Estimate costs
costs = aws.estimate_costs('s3', {
    'storage_gb': 100,
    'requests': 10000,
    'data_transfer_gb': 50
})
print(f"Estimated monthly cost: ${costs['total_usd']}")
```

### MCP Tools (for AI Assistants)

When the MCP server is running, use these tools:

```
aws_list_s3_buckets
  → Lists all S3 buckets in your account

aws_list_ec2_instances  
  → Lists all EC2 instances in the region

aws_list_lambda_functions
  → Lists all Lambda functions

aws_best_practices s3
  → Gets AWS best practices for S3

aws_estimate_costs s3 {"storage_gb": 100, "requests": 10000}
  → Estimates S3 costs based on usage
```

## Environment Variables Reference

### Essential
```bash
AWS_REGION=us-east-1           # Required: AWS region
```

### Authentication (choose one)
```bash
# Option 1: Access Keys
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Option 2: AWS Profile
AWS_PROFILE=default

# Option 3: IAM Role (no variables needed)
```

### Optional
```bash
AWS_SESSION_TOKEN=...          # For temporary credentials
AWS_ENDPOINT_URL=...           # For LocalStack testing
AWS_ENFORCE_BEST_PRACTICES=true
AWS_COST_OPTIMIZATION=true
```

## Common Use Cases

### 1. List and Manage S3 Buckets

```python
aws = AWSMCPIntegration()

# List all buckets
buckets = aws.list_s3_buckets()

# List objects in a bucket
objects = aws.list_s3_objects('my-bucket', prefix='data/')

# Upload a file
aws.upload_to_s3('my-bucket', 'local/file.txt', 'remote/file.txt')
```

### 2. Monitor EC2 Instances

```python
# List all instances
instances = aws.list_ec2_instances()
for inst in instances:
    print(f"{inst['InstanceId']}: {inst['State']['Name']}")

# Get specific instance status
status = aws.get_ec2_instance_status('i-1234567890abcdef0')
```

### 3. Invoke Lambda Functions

```python
# List functions
functions = aws.list_lambda_functions()

# Invoke a function
result = aws.invoke_lambda(
    'my-function',
    payload={'key': 'value'}
)
print(result['Payload'])
```

### 4. Get AWS Best Practices

```python
# S3 best practices
s3_tips = aws.get_aws_best_practices('s3')
print("Security tips:", s3_tips['security'])

# EC2 best practices
ec2_tips = aws.get_aws_best_practices('ec2')
print("Cost optimization:", ec2_tips['cost'])

# Lambda best practices
lambda_tips = aws.get_aws_best_practices('lambda')
print("Performance tips:", lambda_tips['performance'])
```

### 5. Estimate AWS Costs

```python
# S3 costs
s3_costs = aws.estimate_costs('s3', {
    'storage_gb': 1000,
    'requests': 100000,
    'data_transfer_gb': 100
})
print(f"S3 monthly cost: ${s3_costs['total_usd']}")

# EC2 costs (t2.micro running 24/7)
ec2_costs = aws.estimate_costs('ec2', {
    'hours': 730  # hours per month
})
print(f"EC2 monthly cost: ${ec2_costs['total_usd']}")

# Lambda costs
lambda_costs = aws.estimate_costs('lambda', {
    'requests': 1000000,
    'gb_seconds': 500000
})
print(f"Lambda monthly cost: ${lambda_costs['total_usd']}")
```

## Testing with LocalStack

Test AWS integrations locally without real AWS credentials:

```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Configure for LocalStack
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

# Now use AWS MCP as normal
```

## Troubleshooting

### "boto3 is not installed"
```bash
pip install boto3 botocore
```

### "Unable to locate credentials"
```bash
# Check environment variables
echo $AWS_REGION
echo $AWS_ACCESS_KEY_ID

# Or configure AWS CLI
aws configure
```

### "Access Denied" errors
```bash
# Check your identity
aws sts get-caller-identity

# Check IAM permissions
# Ensure your user/role has necessary permissions
```

### "AWS configuration is invalid"
Check that you have both access key ID and secret key set:
```bash
# Both must be set together
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

## Security Best Practices

1. ✅ **Use IAM roles** when running on AWS (EC2, ECS, Lambda)
2. ✅ **Never commit credentials** to git (use .env in .gitignore)
3. ✅ **Rotate credentials** regularly
4. ✅ **Use least privilege** IAM policies
5. ✅ **Enable MFA** for AWS console access
6. ✅ **Use temporary credentials** (STS) when possible

## Documentation

- 📖 **Full documentation**: [docs/AWS_MCP.md](./docs/AWS_MCP.md)
- 📖 **Implementation details**: [AWS_MCP_IMPLEMENTATION_SUMMARY.md](./AWS_MCP_IMPLEMENTATION_SUMMARY.md)
- 📖 **AWS setup guide**: [docs/AWS.md](./docs/AWS.md)
- 📖 **Main README**: [README.md](./README.md)

## Getting Help

1. Read the full documentation: `docs/AWS_MCP.md`
2. Run the setup script: `./scripts/setup_aws_mcp.sh`
3. Check the test examples: `tests/test_aws_mcp.py`
4. Review environment variables: `.env.example`

## Next Steps

After setup:
1. ✅ Start the MCP server: `python -m mcp_project_orchestrator.project_orchestration`
2. ✅ Connect your AI assistant (Claude Desktop, etc.)
3. ✅ Use AWS MCP tools in conversations
4. ✅ Explore best practices and cost optimization

## Example: Complete Workflow

```python
#!/usr/bin/env python3
"""Complete AWS MCP workflow example."""
from mcp_project_orchestrator.aws_mcp import AWSMCPIntegration, AWSConfig

# Initialize AWS MCP
aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))

# 1. Check what AWS resources you have
print("=== Your AWS Resources ===")
print(f"S3 Buckets: {len(aws.list_s3_buckets())}")
print(f"EC2 Instances: {len(aws.list_ec2_instances())}")
print(f"Lambda Functions: {len(aws.list_lambda_functions())}")

# 2. Get best practices for your services
print("\n=== S3 Best Practices ===")
practices = aws.get_aws_best_practices('s3')
for tip in practices['security'][:3]:
    print(f"  • {tip}")

# 3. Estimate your costs
print("\n=== Cost Estimation ===")
s3_estimate = aws.estimate_costs('s3', {
    'storage_gb': 100,
    'requests': 10000,
    'data_transfer_gb': 50
})
print(f"Estimated S3 cost: ${s3_estimate['total_usd']}/month")

# 4. Take action based on best practices
# ... your code here ...

print("\n✅ Workflow complete!")
```

---

**Ready to start?** Run: `./scripts/setup_aws_mcp.sh`