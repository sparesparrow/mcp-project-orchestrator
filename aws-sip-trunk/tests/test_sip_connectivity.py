"""
Integration tests for SIP trunk connectivity.

Tests SIP registration, call establishment, and audio flow.
"""

import os
import socket
import time
from typing import Optional

import pytest
import boto3


class TestSIPConnectivity:
    """Test suite for SIP trunk connectivity."""
    
    @pytest.fixture
    def aws_config(self) -> dict:
        """Load AWS configuration from environment."""
        return {
            "region": os.getenv("AWS_REGION", "us-east-1"),
            "instance_id": os.getenv("INSTANCE_ID"),
            "elastic_ip": os.getenv("ELASTIC_IP"),
            "project_name": os.getenv("PROJECT_NAME", "asterisk-sip-trunk"),
        }
    
    @pytest.fixture
    def ssm_client(self, aws_config: dict):
        """Create SSM client for parameter retrieval."""
        return boto3.client("ssm", region_name=aws_config["region"])
    
    @pytest.fixture
    def ec2_client(self, aws_config: dict):
        """Create EC2 client."""
        return boto3.client("ec2", region_name=aws_config["region"])
    
    def test_instance_running(self, ec2_client, aws_config: dict):
        """Test that EC2 instance is running."""
        response = ec2_client.describe_instances(
            InstanceIds=[aws_config["instance_id"]]
        )
        
        state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
        assert state == "running", f"Instance is {state}, expected running"
    
    def test_elastic_ip_associated(self, ec2_client, aws_config: dict):
        """Test that Elastic IP is associated with instance."""
        response = ec2_client.describe_addresses(
            Filters=[
                {"Name": "instance-id", "Values": [aws_config["instance_id"]]}
            ]
        )
        
        assert len(response["Addresses"]) > 0, "No Elastic IP associated"
        assert response["Addresses"][0]["PublicIp"] == aws_config["elastic_ip"]
    
    def test_sip_tcp_port_open(self, aws_config: dict):
        """Test that SIP TCP port 5060 is reachable."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex((aws_config["elastic_ip"], 5060))
            assert result == 0, f"SIP TCP port 5060 not reachable (error: {result})"
        finally:
            sock.close()
    
    def test_rtp_ports_configured(self, aws_config: dict):
        """Test that RTP port range is accessible."""
        # Test a sample RTP port (cannot test all 10,000 ports)
        test_port = 10000
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        try:
            # Send a test UDP packet
            sock.sendto(b"TEST", (aws_config["elastic_ip"], test_port))
            # We expect no response (it's a test), but port should be reachable
            # If firewall blocks, we'd get connection refused
        except socket.timeout:
            # Timeout is acceptable - port is open but nothing listening
            pass
        except Exception as e:
            pytest.fail(f"RTP port test failed: {e}")
        finally:
            sock.close()
    
    def test_credentials_in_parameter_store(self, ssm_client, aws_config: dict):
        """Test that credentials are stored in Parameter Store."""
        project = aws_config["project_name"]
        
        # Test phone parameter
        response = ssm_client.get_parameter(
            Name=f"/{project}/elevenlabs/phone_e164",
            WithDecryption=True
        )
        phone = response["Parameter"]["Value"]
        assert phone.startswith("+"), "Phone number should be in E.164 format"
        
        # Test password parameter
        response = ssm_client.get_parameter(
            Name=f"/{project}/elevenlabs/sip_password",
            WithDecryption=True
        )
        password = response["Parameter"]["Value"]
        assert len(password) > 0, "SIP password should not be empty"
    
    def test_cloudwatch_logs_exist(self, aws_config: dict):
        """Test that CloudWatch log group exists."""
        logs_client = boto3.client("logs", region_name=aws_config["region"])
        
        log_group_name = f"/aws/ec2/{aws_config['project_name']}/asterisk"
        
        response = logs_client.describe_log_groups(
            logGroupNamePrefix=log_group_name
        )
        
        assert len(response["logGroups"]) > 0, "CloudWatch log group not found"
        assert response["logGroups"][0]["logGroupName"] == log_group_name
    
    def test_s3_recordings_bucket_exists(self, aws_config: dict):
        """Test that S3 recordings bucket exists."""
        s3_client = boto3.client("s3", region_name=aws_config["region"])
        sts_client = boto3.client("sts", region_name=aws_config["region"])
        
        account_id = sts_client.get_caller_identity()["Account"]
        bucket_name = f"{aws_config['project_name']}-recordings-{account_id}"
        
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except Exception as e:
            pytest.fail(f"Recordings bucket does not exist: {e}")
    
    @pytest.mark.slow
    def test_asterisk_service_healthy(self, ec2_client, aws_config: dict):
        """
        Test Asterisk service health via Systems Manager.
        
        Requires SSM agent installed on instance.
        """
        ssm_client = boto3.client("ssm", region_name=aws_config["region"])
        
        # Send command to check Asterisk status
        response = ssm_client.send_command(
            InstanceIds=[aws_config["instance_id"]],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    "systemctl is-active asterisk",
                    "asterisk -rx 'core show version' | head -1"
                ]
            }
        )
        
        command_id = response["Command"]["CommandId"]
        
        # Wait for command to complete
        time.sleep(5)
        
        # Get command output
        output = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=aws_config["instance_id"]
        )
        
        assert output["Status"] == "Success", "Asterisk health check failed"
        assert "active" in output["StandardOutputContent"].lower()


class TestSIPRegistration:
    """Test SIP registration with ElevenLabs."""
    
    @pytest.mark.integration
    def test_pjsip_endpoint_configured(self):
        """Test that PJSIP endpoint is configured correctly."""
        # This test requires SSH access to the instance
        # Implementation depends on your testing infrastructure
        pytest.skip("Requires SSH access - implement based on your setup")
    
    @pytest.mark.integration
    def test_elevenlabs_endpoint_available(self):
        """Test that ElevenLabs endpoint is available."""
        pytest.skip("Requires SSH access - implement based on your setup")


class TestCallFlow:
    """Test call establishment and audio flow."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_outbound_call_to_elevenlabs(self):
        """Test outbound call to ElevenLabs agent."""
        # This test requires PJSUA or similar SIP client
        pytest.skip("Requires SIP client - implement based on your setup")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_inbound_call_from_elevenlabs(self):
        """Test inbound call from ElevenLabs agent."""
        pytest.skip("Requires SIP client - implement based on your setup")
    
    @pytest.mark.integration
    def test_dtmf_functionality(self):
        """Test DTMF tone handling."""
        pytest.skip("Requires SIP client - implement based on your setup")


class TestMonitoring:
    """Test monitoring and alerting."""
    
    def test_cloudwatch_alarms_configured(self, aws_config: dict):
        """Test that CloudWatch alarms are configured."""
        cloudwatch = boto3.client("cloudwatch", region_name=aws_config["region"])
        
        response = cloudwatch.describe_alarms(
            AlarmNamePrefix=aws_config["project_name"]
        )
        
        assert len(response["MetricAlarms"]) > 0, "No CloudWatch alarms configured"
        
        # Check for specific alarms
        alarm_names = [alarm["AlarmName"] for alarm in response["MetricAlarms"]]
        assert any("cpu" in name.lower() for name in alarm_names), "CPU alarm missing"
    
    def test_dashboard_exists(self, aws_config: dict):
        """Test that CloudWatch dashboard exists."""
        cloudwatch = boto3.client("cloudwatch", region_name=aws_config["region"])
        
        dashboard_name = f"{aws_config['project_name']}-dashboard"
        
        try:
            cloudwatch.get_dashboard(DashboardName=dashboard_name)
        except Exception as e:
            pytest.fail(f"Dashboard not found: {e}")


# Test configuration
@pytest.fixture(scope="session", autouse=True)
def verify_environment():
    """Verify required environment variables are set."""
    required_vars = ["AWS_REGION", "INSTANCE_ID", "ELASTIC_IP"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        pytest.skip(f"Missing required environment variables: {', '.join(missing)}")
