#!/usr/bin/env python3
"""
AWS MCP Integration Module.

This module provides AWS-specific Model Context Protocol capabilities including:
- AWS service integrations (S3, EC2, Lambda, CloudFormation, etc.)
- AWS best practices enforcement
- AWS documentation and guidance
- Cost optimization recommendations
- IAM and security configurations

Environment Variables Required:
- AWS_REGION: AWS region (default: us-east-1)
- AWS_ACCESS_KEY_ID: AWS access key ID (optional if using IAM roles)
- AWS_SECRET_ACCESS_KEY: AWS secret access key (optional if using IAM roles)
- AWS_SESSION_TOKEN: AWS session token (optional for temporary credentials)
- AWS_PROFILE: AWS CLI profile name (optional)
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AWSConfig:
    """
    AWS Configuration for MCP integration.
    
    Attributes:
        region: AWS region (e.g., us-east-1, eu-west-1)
        access_key_id: AWS access key ID (optional if using IAM roles)
        secret_access_key: AWS secret access key (optional if using IAM roles)
        session_token: AWS session token for temporary credentials
        profile: AWS CLI profile name
        endpoint_url: Custom endpoint URL (for testing or LocalStack)
    """
    region: str = field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    access_key_id: Optional[str] = field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID"))
    secret_access_key: Optional[str] = field(
        default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    session_token: Optional[str] = field(default_factory=lambda: os.getenv("AWS_SESSION_TOKEN"))
    profile: Optional[str] = field(default_factory=lambda: os.getenv("AWS_PROFILE"))
    endpoint_url: Optional[str] = field(default_factory=lambda: os.getenv("AWS_ENDPOINT_URL"))

    def to_boto3_config(self) -> Dict[str, Any]:
        """
        Convert AWS config to boto3 client configuration.
        
        Returns:
            Dictionary suitable for boto3.client() or boto3.resource()
        """
        config = {"region_name": self.region}
        
        if self.access_key_id:
            config["aws_access_key_id"] = self.access_key_id
        if self.secret_access_key:
            config["aws_secret_access_key"] = self.secret_access_key
        if self.session_token:
            config["aws_session_token"] = self.session_token
        if self.endpoint_url:
            config["endpoint_url"] = self.endpoint_url
            
        return config

    def validate(self) -> bool:
        """
        Validate AWS configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.region:
            logger.error("AWS_REGION is required")
            return False
            
        # If access_key_id is provided, secret_access_key must also be provided
        if self.access_key_id and not self.secret_access_key:
            logger.error("AWS_SECRET_ACCESS_KEY is required when AWS_ACCESS_KEY_ID is set")
            return False
            
        if self.secret_access_key and not self.access_key_id:
            logger.error("AWS_ACCESS_KEY_ID is required when AWS_SECRET_ACCESS_KEY is set")
            return False
            
        return True


class AWSMCPIntegration:
    """
    AWS MCP Integration providing AWS service capabilities through MCP.
    
    This class provides tools and resources for:
    - AWS service management (S3, EC2, Lambda, etc.)
    - AWS best practices and architectural guidance
    - Cost optimization recommendations
    - Security and IAM configurations
    """
    
    def __init__(self, config: Optional[AWSConfig] = None):
        """
        Initialize AWS MCP integration.
        
        Args:
            config: AWS configuration. If None, loads from environment variables.
        """
        self.config = config or AWSConfig()
        self._boto3_available = False
        self._clients: Dict[str, Any] = {}
        
        # Validate configuration
        if not self.config.validate():
            logger.warning("AWS configuration is invalid. Some features may not work.")
        
        # Try to import boto3
        try:
            import boto3
            self._boto3_available = True
            logger.info("boto3 is available for AWS operations")
        except ImportError:
            logger.warning(
                "boto3 is not installed. Install it with: pip install boto3 botocore"
            )
    
    def _get_client(self, service_name: str):
        """
        Get or create a boto3 client for the specified service.
        
        Args:
            service_name: AWS service name (e.g., 's3', 'ec2', 'lambda')
            
        Returns:
            Boto3 client instance
            
        Raises:
            ImportError: If boto3 is not installed
            Exception: If client creation fails
        """
        if not self._boto3_available:
            raise ImportError("boto3 is not installed")
        
        if service_name not in self._clients:
            import boto3
            
            # Use profile if specified, otherwise use credentials
            if self.config.profile:
                session = boto3.Session(profile_name=self.config.profile)
                self._clients[service_name] = session.client(
                    service_name,
                    region_name=self.config.region,
                    endpoint_url=self.config.endpoint_url
                )
            else:
                self._clients[service_name] = boto3.client(
                    service_name,
                    **self.config.to_boto3_config()
                )
            
            logger.info(f"Created {service_name} client for region {self.config.region}")
        
        return self._clients[service_name]
    
    # S3 Operations
    def list_s3_buckets(self) -> List[Dict[str, Any]]:
        """
        List all S3 buckets in the account.
        
        Returns:
            List of bucket information dictionaries
        """
        try:
            s3 = self._get_client('s3')
            response = s3.list_buckets()
            return response.get('Buckets', [])
        except Exception as e:
            logger.error(f"Error listing S3 buckets: {e}")
            return []
    
    def list_s3_objects(self, bucket_name: str, prefix: str = "") -> List[Dict[str, Any]]:
        """
        List objects in an S3 bucket.
        
        Args:
            bucket_name: Name of the S3 bucket
            prefix: Optional prefix to filter objects
            
        Returns:
            List of object information dictionaries
        """
        try:
            s3 = self._get_client('s3')
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            return response.get('Contents', [])
        except Exception as e:
            logger.error(f"Error listing S3 objects in {bucket_name}: {e}")
            return []
    
    def upload_to_s3(self, bucket_name: str, file_path: str, object_key: str) -> bool:
        """
        Upload a file to S3.
        
        Args:
            bucket_name: Name of the S3 bucket
            file_path: Local file path to upload
            object_key: S3 object key (destination path)
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            s3 = self._get_client('s3')
            s3.upload_file(file_path, bucket_name, object_key)
            logger.info(f"Uploaded {file_path} to s3://{bucket_name}/{object_key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return False
    
    # EC2 Operations
    def list_ec2_instances(self) -> List[Dict[str, Any]]:
        """
        List all EC2 instances in the region.
        
        Returns:
            List of instance information dictionaries
        """
        try:
            ec2 = self._get_client('ec2')
            response = ec2.describe_instances()
            instances = []
            for reservation in response.get('Reservations', []):
                instances.extend(reservation.get('Instances', []))
            return instances
        except Exception as e:
            logger.error(f"Error listing EC2 instances: {e}")
            return []
    
    def get_ec2_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """
        Get the status of an EC2 instance.
        
        Args:
            instance_id: EC2 instance ID
            
        Returns:
            Dictionary with instance status information
        """
        try:
            ec2 = self._get_client('ec2')
            response = ec2.describe_instance_status(InstanceIds=[instance_id])
            statuses = response.get('InstanceStatuses', [])
            return statuses[0] if statuses else {}
        except Exception as e:
            logger.error(f"Error getting EC2 instance status: {e}")
            return {}
    
    # Lambda Operations
    def list_lambda_functions(self) -> List[Dict[str, Any]]:
        """
        List all Lambda functions in the region.
        
        Returns:
            List of Lambda function information dictionaries
        """
        try:
            lambda_client = self._get_client('lambda')
            response = lambda_client.list_functions()
            return response.get('Functions', [])
        except Exception as e:
            logger.error(f"Error listing Lambda functions: {e}")
            return []
    
    def invoke_lambda(
        self,
        function_name: str,
        payload: Dict[str, Any],
        invocation_type: str = "RequestResponse"
    ) -> Dict[str, Any]:
        """
        Invoke a Lambda function.
        
        Args:
            function_name: Name of the Lambda function
            payload: Payload to send to the function
            invocation_type: Type of invocation (RequestResponse, Event, DryRun)
            
        Returns:
            Lambda invocation response
        """
        try:
            lambda_client = self._get_client('lambda')
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )
            
            result = {
                'StatusCode': response['StatusCode'],
                'Payload': response['Payload'].read().decode('utf-8')
            }
            
            if 'FunctionError' in response:
                result['FunctionError'] = response['FunctionError']
            
            return result
        except Exception as e:
            logger.error(f"Error invoking Lambda function: {e}")
            return {'error': str(e)}
    
    # CloudFormation Operations
    def list_cloudformation_stacks(self) -> List[Dict[str, Any]]:
        """
        List all CloudFormation stacks.
        
        Returns:
            List of stack information dictionaries
        """
        try:
            cfn = self._get_client('cloudformation')
            response = cfn.describe_stacks()
            return response.get('Stacks', [])
        except Exception as e:
            logger.error(f"Error listing CloudFormation stacks: {e}")
            return []
    
    # IAM Operations
    def list_iam_users(self) -> List[Dict[str, Any]]:
        """
        List all IAM users.
        
        Returns:
            List of IAM user information dictionaries
        """
        try:
            iam = self._get_client('iam')
            response = iam.list_users()
            return response.get('Users', [])
        except Exception as e:
            logger.error(f"Error listing IAM users: {e}")
            return []
    
    def list_iam_roles(self) -> List[Dict[str, Any]]:
        """
        List all IAM roles.
        
        Returns:
            List of IAM role information dictionaries
        """
        try:
            iam = self._get_client('iam')
            response = iam.list_roles()
            return response.get('Roles', [])
        except Exception as e:
            logger.error(f"Error listing IAM roles: {e}")
            return []
    
    # AWS Best Practices
    def get_aws_best_practices(self, service: str) -> Dict[str, Any]:
        """
        Get AWS best practices for a specific service.
        
        Args:
            service: AWS service name (e.g., 's3', 'ec2', 'lambda')
            
        Returns:
            Dictionary containing best practices and recommendations
        """
        best_practices = {
            's3': {
                'security': [
                    'Enable bucket encryption',
                    'Use bucket policies for access control',
                    'Enable versioning for critical data',
                    'Enable access logging',
                    'Block public access by default'
                ],
                'cost': [
                    'Use appropriate storage classes (Standard, IA, Glacier)',
                    'Enable lifecycle policies',
                    'Delete incomplete multipart uploads',
                    'Use S3 Intelligent-Tiering for unpredictable access patterns'
                ],
                'performance': [
                    'Use CloudFront for content delivery',
                    'Enable Transfer Acceleration for large files',
                    'Use multipart upload for files > 100MB'
                ]
            },
            'ec2': {
                'security': [
                    'Use security groups properly',
                    'Enable detailed monitoring',
                    'Use IAM roles instead of credentials',
                    'Keep AMIs up to date',
                    'Enable EBS encryption'
                ],
                'cost': [
                    'Use Reserved Instances or Savings Plans',
                    'Right-size instances regularly',
                    'Use Auto Scaling',
                    'Stop unused instances',
                    'Use Spot Instances for flexible workloads'
                ],
                'performance': [
                    'Choose appropriate instance types',
                    'Use placement groups for HPC',
                    'Enable enhanced networking',
                    'Use EBS-optimized instances'
                ]
            },
            'lambda': {
                'security': [
                    'Use IAM roles with least privilege',
                    'Enable VPC if accessing private resources',
                    'Use environment variables for configuration',
                    'Enable AWS X-Ray for tracing'
                ],
                'cost': [
                    'Optimize memory allocation',
                    'Reduce cold starts',
                    'Use Lambda Power Tuning',
                    'Monitor and optimize execution time'
                ],
                'performance': [
                    'Reuse execution context',
                    'Minimize deployment package size',
                    'Use Lambda layers for common code',
                    'Configure appropriate timeout values'
                ]
            }
        }
        
        return best_practices.get(
            service.lower(),
            {'message': f'Best practices for {service} not available'}
        )
    
    # Cost Optimization
    def estimate_costs(self, service: str, usage: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate AWS costs for a service based on usage.
        
        Args:
            service: AWS service name
            usage: Dictionary describing usage patterns
            
        Returns:
            Dictionary with cost estimates
        """
        # This is a simplified example. Real implementation would use AWS Pricing API
        estimates = {
            's3': {
                'storage_gb_month': usage.get('storage_gb', 0) * 0.023,
                'requests': usage.get('requests', 0) * 0.0004 / 1000,
                'data_transfer_gb': usage.get('data_transfer_gb', 0) * 0.09
            },
            'ec2': {
                't2.micro_hours': usage.get('hours', 0) * 0.0116
            },
            'lambda': {
                'requests': usage.get('requests', 0) * 0.20 / 1000000,
                'compute_gb_seconds': usage.get('gb_seconds', 0) * 0.0000166667
            }
        }
        
        service_estimate = estimates.get(service.lower(), {})
        total = sum(service_estimate.values()) if service_estimate else 0
        
        return {
            'service': service,
            'breakdown': service_estimate,
            'total_usd': round(total, 2)
        }


def register_aws_mcp_tools(mcp_server):
    """
    Register AWS MCP tools with a FastMCP server instance.
    
    Args:
        mcp_server: FastMCP server instance
    """
    aws = AWSMCPIntegration()
    
    @mcp_server.tool(
        name="aws_list_s3_buckets",
        description="List all S3 buckets in the AWS account"
    )
    def list_s3_buckets() -> str:
        """List all S3 buckets."""
        buckets = aws.list_s3_buckets()
        if not buckets:
            return "No S3 buckets found or unable to list buckets."
        
        result = "S3 Buckets:\n"
        for bucket in buckets:
            result += f"- {bucket['Name']} (Created: {bucket['CreationDate']})\n"
        return result
    
    @mcp_server.tool(
        name="aws_list_ec2_instances",
        description="List all EC2 instances in the current region"
    )
    def list_ec2_instances() -> str:
        """List all EC2 instances."""
        instances = aws.list_ec2_instances()
        if not instances:
            return "No EC2 instances found."
        
        result = "EC2 Instances:\n"
        for instance in instances:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']
            instance_type = instance['InstanceType']
            result += f"- {instance_id} ({instance_type}) - State: {state}\n"
        return result
    
    @mcp_server.tool(
        name="aws_list_lambda_functions",
        description="List all Lambda functions in the current region"
    )
    def list_lambda_functions() -> str:
        """List all Lambda functions."""
        functions = aws.list_lambda_functions()
        if not functions:
            return "No Lambda functions found."
        
        result = "Lambda Functions:\n"
        for func in functions:
            name = func['FunctionName']
            runtime = func['Runtime']
            result += f"- {name} ({runtime})\n"
        return result
    
    @mcp_server.tool(
        name="aws_best_practices",
        description="Get AWS best practices for a specific service (s3, ec2, lambda)"
    )
    def get_best_practices(service: str) -> str:
        """Get AWS best practices for a service."""
        practices = aws.get_aws_best_practices(service)
        
        if 'message' in practices:
            return practices['message']
        
        result = f"AWS Best Practices for {service.upper()}:\n\n"
        
        for category, items in practices.items():
            result += f"{category.upper()}:\n"
            for item in items:
                result += f"  - {item}\n"
            result += "\n"
        
        return result
    
    @mcp_server.tool(
        name="aws_estimate_costs",
        description="Estimate AWS costs based on usage (JSON format)"
    )
    def estimate_costs(service: str, usage_json: str) -> str:
        """Estimate AWS costs."""
        try:
            usage = json.loads(usage_json)
            estimate = aws.estimate_costs(service, usage)
            
            result = f"Cost Estimate for {service.upper()}:\n\n"
            result += f"Breakdown:\n"
            for item, cost in estimate['breakdown'].items():
                result += f"  - {item}: ${cost:.4f}\n"
            result += f"\nTotal: ${estimate['total_usd']} USD\n"
            
            return result
        except json.JSONDecodeError:
            return "Error: Invalid JSON format for usage parameter"
    
    logger.info("AWS MCP tools registered successfully")