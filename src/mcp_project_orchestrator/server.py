"""
MCP Project Orchestrator Server.

This is the main entry point for the MCP Project Orchestrator server.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

from .core import FastMCPServer, MCPConfig, setup_logging
from .prompt_manager import PromptManager
from .mermaid import MermaidGenerator, MermaidRenderer
from .templates import ProjectTemplateManager, ComponentTemplateManager


class ProjectOrchestratorServer:
    """
    MCP Project Orchestrator Server.
    
    This server integrates prompt management, diagram generation, and project templating
    capabilities into a unified MCP server.
    """
    
    def __init__(self, config: MCPConfig):
        """
        Initialize the server with configuration.
        
        Args:
            config: The server configuration
        """
        self.config = config
        self.mcp = FastMCPServer(config=config)
        self.prompt_manager = None
        self.mermaid_service = None
        self.template_manager = None
        self.logger = setup_logging(log_file=config.log_file)
        
    async def initialize(self):
        """Initialize all components and register tools."""
        self.logger.info("Initializing Project Orchestrator Server")
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager(self.config)
        await self.prompt_manager.initialize()
        
        # Initialize mermaid service
        self.mermaid_service = MermaidGenerator(self.config)
        await self.mermaid_service.initialize()
        
        # Initialize template manager
        self.template_manager = {
            "project": ProjectTemplateManager(self.config),
            "component": ComponentTemplateManager(self.config)
        }
        await self.template_manager["project"].initialize()
        await self.template_manager["component"].initialize()
        
        # Register tools
        self._register_tools()
        
        # Initialize MCP server
        await self.mcp.initialize()
        
        self.logger.info("Project Orchestrator Server initialized successfully")
        
    def _register_tools(self):
        """Register all tools with the MCP server."""
        self.logger.info("Registering tools")
        
        # Register prompt rendering tool
        self.mcp.register_tool(
            name="renderPrompt",
            description="Render a prompt template with variables",
            parameters={
                "type": "object",
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": "Name of the template to render"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variables to use for rendering"
                    }
                },
                "required": ["template_name"]
            },
            handler=self._handle_render_prompt
        )
        
        # Register diagram generation tool
        self.mcp.register_tool(
            name="generateDiagram",
            description="Generate a Mermaid diagram",
            parameters={
                "type": "object",
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": "Name of the diagram template"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variables to use for rendering"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["svg", "png", "pdf"],
                        "default": "svg",
                        "description": "Output format for the diagram"
                    }
                },
                "required": ["template_name"]
            },
            handler=self._handle_generate_diagram
        )
        
        # Register project generation tool
        self.mcp.register_tool(
            name="generateProject",
            description="Generate a project from a template",
            parameters={
                "type": "object",
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": "Name of the project template"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variables to use for generation"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory for the project"
                    }
                },
                "required": ["template_name", "output_dir"]
            },
            handler=self._handle_generate_project
        )
        
        # Register component generation tool
        self.mcp.register_tool(
            name="generateComponent",
            description="Generate a component from a template",
            parameters={
                "type": "object",
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": "Name of the component template"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variables to use for generation"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory for the component"
                    }
                },
                "required": ["template_name", "output_dir"]
            },
            handler=self._handle_generate_component
        )
        
    async def _handle_render_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the renderPrompt tool call.
        
        Args:
            params: Tool parameters
            
        Returns:
            Dict with rendered content
        """
        template_name = params["template_name"]
        variables = params.get("variables", {})
        
        try:
            rendered = await self.prompt_manager.render_template(template_name, variables)
            return {"content": rendered}
        except Exception as e:
            self.logger.error(f"Error rendering prompt template: {str(e)}")
            raise
    
    async def _handle_generate_diagram(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the generateDiagram tool call.
        
        Args:
            params: Tool parameters
            
        Returns:
            Dict with diagram URL
        """
        template_name = params["template_name"]
        variables = params.get("variables", {})
        output_format = params.get("output_format", "svg")
        
        try:
            # Generate diagram content
            diagram = self.mermaid_service.generate_from_template(template_name, variables)
            
            # Render to file
            renderer = MermaidRenderer(self.config)
            await renderer.initialize()
            
            output_file = await renderer.render_to_file(
                diagram,
                template_name,
                output_format=output_format
            )
            
            # Create a relative URL
            url = f"/mermaid/{output_file.name}"
            
            return {
                "diagram_url": url,
                "diagram_path": str(output_file)
            }
        except Exception as e:
            self.logger.error(f"Error generating diagram: {str(e)}")
            raise
    
    async def _handle_generate_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the generateProject tool call.
        
        Args:
            params: Tool parameters
            
        Returns:
            Dict with generation result
        """
        template_name = params["template_name"]
        variables = params.get("variables", {})
        output_dir = params["output_dir"]
        
        try:
            # Generate project
            result = await self.template_manager["project"].generate_project(
                template_name,
                variables,
                output_dir
            )
            
            return result
        except Exception as e:
            self.logger.error(f"Error generating project: {str(e)}")
            raise
    
    async def _handle_generate_component(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the generateComponent tool call.
        
        Args:
            params: Tool parameters
            
        Returns:
            Dict with generation result
        """
        template_name = params["template_name"]
        variables = params.get("variables", {})
        output_dir = params["output_dir"]
        
        try:
            # Generate component
            result = await self.template_manager["component"].generate_component(
                template_name,
                variables,
                output_dir
            )
            
            return result
        except Exception as e:
            self.logger.error(f"Error generating component: {str(e)}")
            raise
    
    async def handle_client_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle client messages.
        
        Args:
            message: The client message
            
        Returns:
            Response message
        """
        try:
            return await self.mcp.handle_message(message)
        except Exception as e:
            self.logger.error(f"Error handling client message: {str(e)}")
            
            # Create an error response
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def start(self):
        """Start the server."""
        await self.mcp.start()
        
    async def stop(self):
        """Stop the server."""
        await self.mcp.stop()


# Convenience function for starting the server
async def start_server(config_path: Optional[str] = None):
    """
    Start the MCP Project Orchestrator server.
    
    Args:
        config_path: Path to configuration file (optional)
    """
    # Load configuration
    config = MCPConfig(config_file=config_path)
    
    # Create and initialize the server
    server = ProjectOrchestratorServer(config)
    await server.initialize()
    
    # Start the server
    await server.start()
    
    return server
