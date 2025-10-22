# AWS MCP Integration Guide

This document describes the AWS Model Context Protocol (MCP) integration capabilities added to the MCP Project Orchestrator.

## Overview

The AWS MCP integration provides AI-powered access to AWS services, best practices, and cost optimization recommendations through the Model Context Protocol. This enables AI assistants like Claude to interact with AWS services, provide architectural guidance, and help with cloud development tasks.

## Features

### 1. AWS Service Integration
- **S3**: List buckets, upload/download files, manage objects
- **EC2**: List instances, check status, manage compute resources
- **Lambda**: List functions, invoke functions, manage serverless applications
- **CloudFormation**: List and manage infrastructure stacks
- **IAM**: List users, roles, and manage access control

### 2. AWS Best Practices
- Security best practices for each service
- Cost optimization recommendations
- Performance optimization guidelines
- Compliance and governance guidance

### 3. Cost Estimation
- Estimate AWS costs based on usage patterns
- Service-specific cost breakdowns
- Proactive cost optimization suggestions

### 4. Documentation and Guidance
- Access to AWS service documentation
- Contextually relevant code examples
- Ready-to-use CDK constructs and patterns

## Environment Variables

Configure AWS MCP integration using the following environment variables:

### Required
```bash
# AWS Region
AWS_REGION=us-east-1
```

### Optional (for AWS API access)
```bash
# AWS Credentials (if not using IAM roles)
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key

# AWS Session Token (for temporary credentials)
AWS_SESSION_TOKEN=your_session_token

# AWS Profile (use named profile from ~/.aws/credentials)
AWS_PROFILE=default

# AWS Endpoint URL (for testing with LocalStack)
AWS_ENDPOINT_URL=http://localhost:4566
```

### Feature Flags
```bash
# Enable AWS best practices enforcement
AWS_ENFORCE_BEST_PRACTICES=true

# Enable cost optimization recommendations
AWS_COST_OPTIMIZATION=true

# Enable security scanning
AWS_SECURITY_SCANNING=false
```

## Setup

### 1. Install Dependencies

Install the AWS MCP integration dependencies:

```bash
# Install with AWS support
pip install -e ".[aws]"

# Or install boto3 separately
pip install boto3 botocore
```

### 2. Configure Environment Variables

Create a `.env` file in your project root (use `.env.example` as a template):

```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

### 3. Configure AWS Credentials

Choose one of the following methods:

#### Method A: Environment Variables
```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

#### Method B: AWS CLI Profile
```bash
aws configure --profile myprofile
export AWS_PROFILE=myprofile
export AWS_REGION=us-east-1
```

#### Method C: IAM Roles (Recommended for EC2/ECS/Lambda)
When running on AWS infrastructure, use IAM roles instead of credentials:
```bash
export AWS_REGION=us-east-1
# No credentials needed - IAM role provides access
```

## Usage

### Available MCP Tools

Once configured, the following AWS MCP tools are available:

#### 1. `aws_list_s3_buckets`
List all S3 buckets in your AWS account.

**Example:**
```
Use aws_list_s3_buckets to see my S3 buckets
```

#### 2. `aws_list_ec2_instances`
List all EC2 instances in the current region.

**Example:**
```
Show me all EC2 instances using aws_list_ec2_instances
```

#### 3. `aws_list_lambda_functions`
List all Lambda functions in the current region.

**Example:**
```
List my Lambda functions with aws_list_lambda_functions
```

#### 4. `aws_best_practices`
Get AWS best practices for a specific service.

**Parameters:**
- `service`: Service name (s3, ec2, lambda)

**Example:**
```
Get AWS best practices for S3
```

**Returns best practices in categories:**
- Security
- Cost optimization
- Performance

#### 5. `aws_estimate_costs`
Estimate AWS costs based on usage.

**Parameters:**
- `service`: AWS service name
- `usage_json`: JSON string with usage details

**Example:**
```
Estimate S3 costs for {"storage_gb": 100, "requests": 10000, "data_transfer_gb": 50}
```

### Python API

Use the AWS MCP integration directly in Python:

```python
from mcp_project_orchestrator.aws_mcp import AWSMCPIntegration, AWSConfig

# Initialize with default config (from environment variables)
aws = AWSMCPIntegration()

# Or provide custom config
config = AWSConfig(
    region="us-west-2",
    profile="myprofile"
)
aws = AWSMCPIntegration(config)

# List S3 buckets
buckets = aws.list_s3_buckets()
for bucket in buckets:
    print(f"Bucket: {bucket['Name']}")

# Get best practices
practices = aws.get_aws_best_practices("s3")
print(practices)

# Estimate costs
costs = aws.estimate_costs("s3", {
    "storage_gb": 100,
    "requests": 10000,
    "data_transfer_gb": 50
})
print(f"Estimated cost: ${costs['total_usd']}")
```

## AWS Best Practices

The integration includes built-in best practices for common AWS services:

### S3 Best Practices
- **Security**: Enable encryption, bucket policies, versioning, access logging
- **Cost**: Use appropriate storage classes, lifecycle policies, delete incomplete uploads
- **Performance**: Use CloudFront CDN, Transfer Acceleration, multipart upload

### EC2 Best Practices
- **Security**: Proper security groups, detailed monitoring, IAM roles, EBS encryption
- **Cost**: Reserved Instances, right-sizing, Auto Scaling, Spot Instances
- **Performance**: Appropriate instance types, placement groups, enhanced networking

### Lambda Best Practices
- **Security**: Least privilege IAM roles, VPC configuration, environment variables
- **Cost**: Optimize memory, reduce cold starts, monitor execution time
- **Performance**: Reuse execution context, minimize package size, use Lambda layers

## Cost Estimation

The AWS MCP integration provides cost estimation capabilities:

### S3 Cost Estimation
```python
costs = aws.estimate_costs("s3", {
    "storage_gb": 100,      # Storage in GB per month
    "requests": 10000,      # Number of requests
    "data_transfer_gb": 50  # Data transfer in GB
})
# Returns breakdown and total cost
```

### EC2 Cost Estimation
```python
costs = aws.estimate_costs("ec2", {
    "hours": 730  # Hours per month (730 = 24/7)
})
```

### Lambda Cost Estimation
```python
costs = aws.estimate_costs("lambda", {
    "requests": 1000000,      # Number of invocations
    "gb_seconds": 500000      # GB-seconds of compute
})
```

## Security Considerations

### 1. Credential Management
- **Never commit credentials to version control**
- Use `.env` files (add to `.gitignore`)
- Prefer IAM roles over access keys
- Use temporary credentials (STS) when possible
- Rotate credentials regularly

### 2. IAM Permissions
Grant minimum required permissions. Example IAM policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "ec2:DescribeInstances",
        "lambda:ListFunctions",
        "cloudformation:DescribeStacks"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Network Security
- Use VPC endpoints for private connectivity
- Enable AWS CloudTrail for audit logging
- Use AWS Config for compliance monitoring

## Troubleshooting

### Issue: "boto3 is not installed"
**Solution:** Install boto3:
```bash
pip install boto3 botocore
```

### Issue: "AWS configuration is invalid"
**Solution:** Check your environment variables:
```bash
echo $AWS_REGION
echo $AWS_ACCESS_KEY_ID
```

### Issue: "Unable to locate credentials"
**Solution:** Ensure credentials are configured:
```bash
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Issue: Access Denied errors
**Solution:** Check IAM permissions:
```bash
aws sts get-caller-identity
# Verify the identity and attached policies
```

## Advanced Usage

### Using with LocalStack

Test AWS integrations locally with LocalStack:

```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Configure environment
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
```

### Multi-Region Support

Work with multiple AWS regions:

```python
# Create separate integrations for different regions
us_east = AWSMCPIntegration(AWSConfig(region="us-east-1"))
eu_west = AWSMCPIntegration(AWSConfig(region="eu-west-1"))

# List buckets in each region
us_buckets = us_east.list_s3_buckets()
eu_buckets = eu_west.list_s3_buckets()
```

### Cross-Account Access

Use AssumeRole for cross-account access:

```python
import boto3

# Assume role in another account
sts = boto3.client('sts')
response = sts.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/MyRole',
    RoleSessionName='mcp-session'
)

# Use temporary credentials
config = AWSConfig(
    region="us-east-1",
    access_key_id=response['Credentials']['AccessKeyId'],
    secret_access_key=response['Credentials']['SecretAccessKey'],
    session_token=response['Credentials']['SessionToken']
)

aws = AWSMCPIntegration(config)
```

## References

- [AWS MCP Documentation](https://awslabs.github.io/mcp/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS SDK for Python (Boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)

## Contributing

To add new AWS service integrations:

1. Add methods to `AWSMCPIntegration` class in `aws_mcp.py`
2. Add corresponding MCP tools in `register_aws_mcp_tools()`
3. Add best practices to `get_aws_best_practices()`
4. Update this documentation

Example:
```python
def list_dynamodb_tables(self) -> List[Dict[str, Any]]:
    """List all DynamoDB tables."""
    try:
        dynamodb = self._get_client('dynamodb')
        response = dynamodb.list_tables()
        return response.get('TableNames', [])
    except Exception as e:
        logger.error(f"Error listing DynamoDB tables: {e}")
        return []
```

## License

This AWS MCP integration is part of the MCP Project Orchestrator and is licensed under the MIT License.