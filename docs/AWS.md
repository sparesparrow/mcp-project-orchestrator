# AWS Integration

This document covers AWS integration capabilities for the MCP Project Orchestrator.

## AWS MCP Integration

The MCP Project Orchestrator includes comprehensive AWS MCP (Model Context Protocol) integration that enables AI-powered access to AWS services. For detailed information, see [AWS_MCP.md](./AWS_MCP.md).

### Quick Start

1. Install AWS dependencies:
   ```bash
   pip install -e ".[aws]"
   ```

2. Configure AWS credentials:
   ```bash
   export AWS_REGION=us-east-1
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. Start the MCP server with AWS integration enabled.

### Features

- **AWS Service Access**: S3, EC2, Lambda, CloudFormation, IAM
- **Best Practices**: Security, cost optimization, performance guidelines
- **Cost Estimation**: Predict AWS costs based on usage
- **Documentation**: Contextual AWS guidance and examples

See [AWS_MCP.md](./AWS_MCP.md) for complete documentation.

## AWS Artifacts and Container Publishing

This project uses GitHub OIDC to assume an AWS role for publishing artifacts.

### Required AWS setup

- Create S3 bucket: `mcp-orchestrator-artifacts`
- Create ECR repository: `mcp-project-orchestrator`
- Create an IAM role with trust policy for GitHub OIDC and permissions to push to ECR and write to S3. Save its ARN as GitHub secret `AWS_OIDC_ROLE_ARN`.

### Release workflow

On GitHub release publish:
- Build and push container image to ECR using Podman
- Build Python dists and upload to S3 under `releases/<tag>/`
- Optionally archive Conan cache to S3

See `.github/workflows/release.yml`.
