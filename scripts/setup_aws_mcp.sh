#!/bin/bash
# Setup script for AWS MCP integration
# This script helps configure AWS credentials and test the integration

set -e

echo "======================================"
echo "AWS MCP Integration Setup"
echo "======================================"
echo ""

# Check if boto3 is installed
if ! python3 -c "import boto3" 2>/dev/null; then
    echo "❌ boto3 is not installed"
    echo "Installing boto3 and botocore..."
    pip install boto3 botocore
    echo "✅ boto3 installed successfully"
else
    echo "✅ boto3 is already installed"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  Please edit .env file and add your AWS credentials"
    echo "    Required variables:"
    echo "    - AWS_REGION"
    echo "    - AWS_ACCESS_KEY_ID (optional if using IAM roles)"
    echo "    - AWS_SECRET_ACCESS_KEY (optional if using IAM roles)"
    echo ""
    echo "You can also use AWS CLI profiles by setting AWS_PROFILE"
else
    echo "✅ .env file already exists"
fi

# Check if AWS CLI is configured
echo ""
echo "Checking AWS CLI configuration..."
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI is installed"
    
    if aws sts get-caller-identity &> /dev/null; then
        echo "✅ AWS credentials are configured"
        echo ""
        echo "Current AWS Identity:"
        aws sts get-caller-identity
    else
        echo "⚠️  AWS CLI is not configured or credentials are invalid"
        echo ""
        echo "To configure AWS CLI, run:"
        echo "    aws configure"
        echo ""
        echo "Or use environment variables in .env file"
    fi
else
    echo "⚠️  AWS CLI is not installed"
    echo "   Install it from: https://aws.amazon.com/cli/"
fi

# Test AWS MCP integration
echo ""
echo "======================================"
echo "Testing AWS MCP Integration"
echo "======================================"
echo ""

# Create a test script
cat > /tmp/test_aws_mcp.py << 'EOF'
"""Test AWS MCP integration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Loading AWS MCP integration...")
try:
    from mcp_project_orchestrator.aws_mcp import AWSConfig, AWSMCPIntegration
    
    # Check configuration
    config = AWSConfig()
    print(f"✅ AWS Region: {config.region}")
    
    if config.validate():
        print("✅ AWS configuration is valid")
    else:
        print("⚠️  AWS configuration validation failed")
        print("   Check your environment variables")
    
    # Initialize integration
    aws = AWSMCPIntegration(config)
    print("✅ AWS MCP integration initialized")
    
    # Test best practices
    print("\nTesting AWS best practices...")
    practices = aws.get_aws_best_practices('s3')
    print(f"✅ Retrieved {len(practices)} best practice categories for S3")
    
    # Test cost estimation
    print("\nTesting cost estimation...")
    estimate = aws.estimate_costs('s3', {'storage_gb': 100, 'requests': 10000})
    print(f"✅ Cost estimate: ${estimate['total_usd']} USD")
    
    print("\n" + "="*50)
    print("✅ All tests passed!")
    print("="*50)
    print("\nAWS MCP integration is ready to use.")
    print("\nAvailable MCP tools:")
    print("  - aws_list_s3_buckets")
    print("  - aws_list_ec2_instances")
    print("  - aws_list_lambda_functions")
    print("  - aws_best_practices")
    print("  - aws_estimate_costs")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you have installed the package:")
    print("    pip install -e .[aws]")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
EOF

# Run the test
python3 /tmp/test_aws_mcp.py

# Cleanup
rm /tmp/test_aws_mcp.py

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your AWS credentials (if needed)"
echo "2. Run the MCP server: python -m mcp_project_orchestrator.project_orchestration"
echo "3. Use AWS MCP tools in your AI assistant"
echo ""
echo "Documentation:"
echo "  - See docs/AWS_MCP.md for detailed usage"
echo "  - See .env.example for all configuration options"
echo ""