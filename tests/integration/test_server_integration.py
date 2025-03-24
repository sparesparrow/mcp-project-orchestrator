"""
Integration tests for the MCP Project Orchestrator server.

These tests verify that all components work together correctly in the server.
"""

import os
import pytest
import tempfile
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock

from mcp_project_orchestrator.core import MCPConfig
from mcp_project_orchestrator.server import ProjectOrchestratorServer


class TestServerIntegration:
    """Integration tests for the MCP Project Orchestrator server."""
    
    @pytest.fixture
    def temp_server_dir(self):
        """Create a temporary server directory with all required subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            server_dir = Path(temp_dir)
            
            # Create required directories
            (server_dir / "prompts").mkdir(exist_ok=True)
            (server_dir / "templates").mkdir(exist_ok=True)
            (server_dir / "mermaid").mkdir(exist_ok=True)
            (server_dir / "mermaid" / "templates").mkdir(exist_ok=True)
            (server_dir / "mermaid" / "output").mkdir(exist_ok=True)
            (server_dir / "resources").mkdir(exist_ok=True)
            
            yield server_dir
    
    @pytest.fixture
    def config(self, temp_server_dir):
        """Create a test configuration."""
        config_data = {
            "name": "test-orchestrator",
            "version": "0.1.0",
            "description": "Test Project Orchestrator",
            "server": {
                "host": "127.0.0.1",
                "port": 8080
            },
            "paths": {
                "prompts": str(temp_server_dir / "prompts"),
                "templates": str(temp_server_dir / "templates"),
                "mermaid_templates": str(temp_server_dir / "mermaid" / "templates"),
                "mermaid_output": str(temp_server_dir / "mermaid" / "output"),
                "resources": str(temp_server_dir / "resources")
            }
        }
        
        config_file = temp_server_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)
            
        return MCPConfig(config_file=config_file)
    
    @pytest.fixture
    def sample_prompt_template(self, temp_server_dir):
        """Create a sample prompt template."""
        template = {
            "name": "project-description",
            "description": "A template for describing projects",
            "template": "# {{ project_name }}\n\n{{ project_description }}\n\n## Features\n\n{{ features }}",
            "variables": {
                "project_name": {
                    "type": "string",
                    "description": "The name of the project"
                },
                "project_description": {
                    "type": "string",
                    "description": "A brief description of the project"
                },
                "features": {
                    "type": "string",
                    "description": "Key features of the project"
                }
            },
            "category": "documentation",
            "tags": ["project", "documentation"]
        }
        
        template_file = temp_server_dir / "prompts" / "project-description.json"
        with open(template_file, "w") as f:
            json.dump(template, f)
            
        return template
    
    @pytest.fixture
    def sample_mermaid_template(self, temp_server_dir):
        """Create a sample mermaid template."""
        template = {
            "name": "simple-flowchart",
            "type": "flowchart",
            "content": "flowchart TD\n    A[{start}] --> B[{process}]\n    B --> C[{end}]",
            "variables": {
                "start": "Start",
                "process": "Process",
                "end": "End"
            }
        }
        
        template_file = temp_server_dir / "mermaid" / "templates" / "simple-flowchart.json"
        with open(template_file, "w") as f:
            json.dump(template, f)
            
        return template
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, config, sample_prompt_template, sample_mermaid_template):
        """Test that the server initializes properly with all components."""
        # Mock the CLI path check for mermaid
        with patch("pathlib.Path.exists", return_value=True):
            server = ProjectOrchestratorServer(config=config)
            await server.initialize()
            
            # Check if the components were initialized
            assert server.prompt_manager is not None
            assert server.mermaid_service is not None
            assert server.template_manager is not None
            
    @pytest.mark.asyncio
    async def test_prompt_rendering_tool(self, config, sample_prompt_template):
        """Test that the prompt rendering tool works."""
        with patch("pathlib.Path.exists", return_value=True):
            server = ProjectOrchestratorServer(config=config)
            await server.initialize()
            
            # Get the registered tool
            render_prompt_tool = server.mcp.tools.get("renderPrompt")
            assert render_prompt_tool is not None
            
            # Call the tool
            params = {
                "template_name": "project-description",
                "variables": {
                    "project_name": "Test Project",
                    "project_description": "A project for testing",
                    "features": "- Feature 1\n- Feature 2"
                }
            }
            
            result = await render_prompt_tool["handler"](params)
            
            # Check the result
            assert result is not None
            assert "# Test Project" in result["content"]
            assert "A project for testing" in result["content"]
            assert "- Feature 1" in result["content"]
            assert "- Feature 2" in result["content"]
    
    @pytest.mark.asyncio
    async def test_mermaid_generation_tool(self, config, sample_mermaid_template):
        """Test that the mermaid generation tool works."""
        with patch("pathlib.Path.exists", return_value=True):
            # Mock the renderer to avoid actual CLI calls
            async def mock_render(*args, **kwargs):
                return Path(config.mermaid_output_dir) / "test-diagram.svg"
                
            with patch("mcp_project_orchestrator.mermaid.MermaidRenderer.render_to_file", 
                       AsyncMock(side_effect=mock_render)):
                server = ProjectOrchestratorServer(config=config)
                await server.initialize()
                
                # Get the registered tool
                generate_diagram_tool = server.mcp.tools.get("generateDiagram")
                assert generate_diagram_tool is not None
                
                # Call the tool
                params = {
                    "template_name": "simple-flowchart",
                    "variables": {
                        "start": "Begin",
                        "process": "Transform",
                        "end": "Finish"
                    },
                    "output_format": "svg"
                }
                
                result = await generate_diagram_tool["handler"](params)
                
                # Check the result
                assert result is not None
                assert "diagram_url" in result
                
    @pytest.mark.asyncio
    async def test_client_message_handling(self, config, sample_prompt_template, sample_mermaid_template):
        """Test that the server handles client messages properly."""
        with patch("pathlib.Path.exists", return_value=True):
            server = ProjectOrchestratorServer(config=config)
            await server.initialize()
            
            # Create a mock initialize message
            initialize_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "mcp/initialize",
                "params": {
                    "capabilities": {}
                }
            }
            
            # Handle the message
            response = await server.handle_client_message(initialize_msg)
            
            # Check the response
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "result" in response
            assert "capabilities" in response["result"]
            
            # Create a mock listTools message
            list_tools_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "mcp/listTools"
            }
            
            # Handle the message
            response = await server.handle_client_message(list_tools_msg)
            
            # Check the response
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 2
            assert "result" in response
            assert "tools" in response["result"]
            
            # Check if our tools are in the list
            tool_names = [tool["name"] for tool in response["result"]["tools"]]
            assert "renderPrompt" in tool_names
            assert "generateDiagram" in tool_names
            
    @pytest.mark.asyncio
    async def test_error_handling(self, config):
        """Test that the server handles errors properly."""
        with patch("pathlib.Path.exists", return_value=True):
            server = ProjectOrchestratorServer(config=config)
            await server.initialize()
            
            # Create an invalid message
            invalid_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "invalid/method"
            }
            
            # Handle the message
            response = await server.handle_client_message(invalid_msg)
            
            # Check the error response
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "error" in response
            assert response["error"]["code"] == -32601  # Method not found
            
            # Create a valid method but with invalid params
            invalid_params_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "mcp/callTool",
                "params": {
                    "name": "renderPrompt",
                    "params": {
                        "template_name": "non-existent-template",
                        "variables": {}
                    }
                }
            }
            
            # Handle the message
            response = await server.handle_client_message(invalid_params_msg)
            
            # Check the error response
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 2
            assert "error" in response
```