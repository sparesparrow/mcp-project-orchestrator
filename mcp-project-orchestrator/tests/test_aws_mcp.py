"""
Tests for AWS MCP integration.

This module contains unit tests for the AWS MCP integration,
including configuration validation, service operations, and best practices.
"""
import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_project_orchestrator.aws_mcp import (
    AWSConfig,
    AWSMCPIntegration
)


class TestAWSConfig:
    """Test AWS configuration validation and conversion."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = AWSConfig(region='us-east-1')
        assert config.region == 'us-east-1'
        assert config.validate() is True
    
    def test_config_with_credentials(self):
        """Test configuration with credentials."""
        config = AWSConfig(
            region='us-west-2',
            access_key_id='test_key',
            secret_access_key='test_secret'
        )
        assert config.region == 'us-west-2'
        assert config.access_key_id == 'test_key'
        assert config.secret_access_key == 'test_secret'
        assert config.validate() is True
    
    def test_config_validation_missing_secret_key(self):
        """Test validation fails when secret key is missing."""
        config = AWSConfig(
            region='us-east-1',
            access_key_id='key',
            secret_access_key=None
        )
        assert config.validate() is False
    
    def test_to_boto3_config(self):
        """Test conversion to boto3 configuration."""
        config = AWSConfig(
            region='eu-west-1',
            access_key_id='key',
            secret_access_key='secret'
        )
        boto3_config = config.to_boto3_config()
        assert boto3_config['region_name'] == 'eu-west-1'
        assert boto3_config['aws_access_key_id'] == 'key'
        assert boto3_config['aws_secret_access_key'] == 'secret'


class TestAWSMCPIntegration:
    """Test AWS MCP integration."""
    
    def test_initialization(self):
        """Test AWS MCP integration initialization."""
        config = AWSConfig(region='us-east-1')
        aws = AWSMCPIntegration(config)
        assert aws.config.region == 'us-east-1'
    
    def test_get_best_practices_s3(self):
        """Test getting S3 best practices."""
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        practices = aws.get_aws_best_practices('s3')
        
        assert 'security' in practices
        assert 'cost' in practices
        assert 'performance' in practices
        assert len(practices['security']) > 0
    
    def test_get_best_practices_ec2(self):
        """Test getting EC2 best practices."""
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        practices = aws.get_aws_best_practices('ec2')
        
        assert 'security' in practices
        assert 'cost' in practices
        assert 'performance' in practices
    
    def test_get_best_practices_lambda(self):
        """Test getting Lambda best practices."""
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        practices = aws.get_aws_best_practices('lambda')
        
        assert 'security' in practices
        assert 'cost' in practices
        assert 'performance' in practices
    
    def test_estimate_costs_s3(self):
        """Test S3 cost estimation."""
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        estimate = aws.estimate_costs('s3', {
            'storage_gb': 100,
            'requests': 10000,
            'data_transfer_gb': 50
        })
        
        assert estimate['service'] == 's3'
        assert 'breakdown' in estimate
        assert 'total_usd' in estimate
        assert estimate['total_usd'] > 0
    
    def test_estimate_costs_ec2(self):
        """Test EC2 cost estimation."""
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        estimate = aws.estimate_costs('ec2', {
            'hours': 730
        })
        
        assert estimate['service'] == 'ec2'
        assert 'breakdown' in estimate
        assert 'total_usd' in estimate
    
    def test_estimate_costs_lambda(self):
        """Test Lambda cost estimation."""
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        estimate = aws.estimate_costs('lambda', {
            'requests': 1000000,
            'gb_seconds': 500000
        })
        
        assert estimate['service'] == 'lambda'
        assert 'breakdown' in estimate
        assert 'total_usd' in estimate
    
    @patch('mcp_project_orchestrator.aws_mcp.AWSMCPIntegration._get_client')
    def test_list_s3_buckets(self, mock_get_client):
        """Test listing S3 buckets."""
        mock_s3 = Mock()
        mock_s3.list_buckets.return_value = {
            'Buckets': [
                {'Name': 'bucket1', 'CreationDate': '2024-01-01'},
                {'Name': 'bucket2', 'CreationDate': '2024-01-02'}
            ]
        }
        mock_get_client.return_value = mock_s3
        
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        aws._boto3_available = True
        buckets = aws.list_s3_buckets()
        
        assert len(buckets) == 2
        assert buckets[0]['Name'] == 'bucket1'
    
    @patch('mcp_project_orchestrator.aws_mcp.AWSMCPIntegration._get_client')
    def test_list_ec2_instances(self, mock_get_client):
        """Test listing EC2 instances."""
        mock_ec2 = Mock()
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'State': {'Name': 'running'},
                            'InstanceType': 't2.micro'
                        }
                    ]
                }
            ]
        }
        mock_get_client.return_value = mock_ec2
        
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        aws._boto3_available = True
        instances = aws.list_ec2_instances()
        
        assert len(instances) == 1
        assert instances[0]['InstanceId'] == 'i-1234567890abcdef0'
    
    @patch('mcp_project_orchestrator.aws_mcp.AWSMCPIntegration._get_client')
    def test_list_lambda_functions(self, mock_get_client):
        """Test listing Lambda functions."""
        mock_lambda = Mock()
        mock_lambda.list_functions.return_value = {
            'Functions': [
                {
                    'FunctionName': 'my-function',
                    'Runtime': 'python3.9'
                }
            ]
        }
        mock_get_client.return_value = mock_lambda
        
        aws = AWSMCPIntegration(AWSConfig(region='us-east-1'))
        aws._boto3_available = True
        functions = aws.list_lambda_functions()
        
        assert len(functions) == 1
        assert functions[0]['FunctionName'] == 'my-function'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])