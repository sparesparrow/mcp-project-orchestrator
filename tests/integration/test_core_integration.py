"""
Integration tests for the core module functionality.

These tests verify that the core components work together properly.
"""

import os
import pytest
import tempfile
from pathlib import Path
import json

from mcp_project_orchestrator.core import FastMCPServer, MCPConfig
from mcp_project_orchestrator.core import setup_logging, MCPException


class TestCoreIntegration:
    """Integration tests for core module components."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config(self, temp_config_dir):
        """Create a test configuration."""
        config_data = {
            "name": "test-mcp-server",
            "version": "0.1.0",
            "description": "Test MCP Server",
            "server": {
                "host": "127.0.0.1",
                "port": 8080
            },
            "paths": {
                "prompts": str(temp_config_dir / "prompts"),
                "templates": str(temp_config_dir / "templates"),
                "mermaid": str(temp_config_dir / "mermaid"),
                "resources": str(temp_config_dir / "resources")
            }
        }
        
        config_file = temp_config_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Create required directories
        for dir_name in ["prompts", "templates", "mermaid", "resources"]:
            (temp_config_dir / dir_name).mkdir(exist_ok=True)
            
        return MCPConfig(config_file=config_file)
    
    def test_config_loading(self, config):
        """Test that configuration is loaded properly."""
        assert config.name == "test-mcp-server"
        assert config.version == "0.1.0"
        assert config.description == "Test MCP Server"
        assert config.server_host == "127.0.0.1"
        assert config.server_port == 8080
        
    def test_server_initialization(self, config):
        """Test that the server initializes properly."""
        server = FastMCPServer(config=config)
        assert server.name == config.name
        assert server.config == config
        
    def test_tool_registration(self, config):
        """Test that tools can be registered."""
        server = FastMCPServer(config=config)
        
        tool_name = "test-tool"
        tool_description = "A test tool"
        tool_params = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "number"}
            },
            "required": ["param1"]
        }
        
        # Define a simple tool function
        def tool_function(params):
            return {"result": f"Hello, {params['param1']}!"}
        
        # Register the tool
        server.register_tool(
            name=tool_name,
            description=tool_description,
            parameters=tool_params,
            handler=tool_function
        )
        
        # Check if the tool was registered
        assert tool_name in server.tools
        assert server.tools[tool_name]["description"] == tool_description
        assert server.tools[tool_name]["parameters"] == tool_params
        assert server.tools[tool_name]["handler"] == tool_function
        
    def test_resource_registration(self, config):
        """Test that resources can be registered."""
        server = FastMCPServer(config=config)
        
        resource_name = "test-resource"
        resource_content = {"key": "value"}
        
        # Register the resource
        server.register_resource(
            name=resource_name,
            content=resource_content
        )
        
        # Check if the resource was registered
        assert resource_name in server.resources
        assert server.resources[resource_name] == resource_content
        
    def test_exception_handling(self):
        """Test that exceptions are handled properly."""
        with pytest.raises(MCPException) as excinfo:
            raise MCPException("Test exception")
        assert "Test exception" in str(excinfo.value)
        
    def test_logging_setup(self, temp_config_dir):
        """Test that logging is set up properly."""
        log_file = temp_config_dir / "test.log"
        logger = setup_logging(log_file=log_file)
        
        # Log a test message
        test_message = "Test log message"
        logger.info(test_message)
        
        # Check if the message was logged
        with open(log_file, "r") as f:
            log_content = f.read()
        assert test_message in log_content 