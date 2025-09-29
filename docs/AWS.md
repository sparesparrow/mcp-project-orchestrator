# AWS Artifacts and Container Publishing

This project uses GitHub OIDC to assume an AWS role for publishing artifacts.

## Required AWS setup

- Create S3 bucket: `mcp-orchestrator-artifacts`
- Create ECR repository: `mcp-project-orchestrator`
- Create an IAM role with trust policy for GitHub OIDC and permissions to push to ECR and write to S3. Save its ARN as GitHub secret `AWS_OIDC_ROLE_ARN`.

## Release workflow

On GitHub release publish:
- Build and push container image to ECR using Podman
- Build Python dists and upload to S3 under `releases/<tag>/`
- Optionally archive Conan cache to S3

See `.github/workflows/release.yml`.
