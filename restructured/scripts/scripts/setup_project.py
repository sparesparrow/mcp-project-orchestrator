#!/usr/bin/env python3
"""
MCP Project Orchestrator Setup Script.

This script orchestrates the setup of the MCP Project Orchestrator by:
1. Setting up the project directory structure
2. Running all consolidation scripts for prompts, templates, resources, and mermaid diagrams
3. Creating initial configuration files
4. Setting up proper imports and exports

Usage:
    python3 setup_project.py
"""

import os
import sys
import subprocess
import json
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root directory
PROJECT_ROOT = Path("/home/sparrow/projects/mcp-project-orchestrator")

# Source directory
SRC_DIR = PROJECT_ROOT / "src" / "mcp_project_orchestrator"

# Scripts directory
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Consolidation scripts
CONSOLIDATION_SCRIPTS = [
    SCRIPTS_DIR / "consolidate_prompts.py",
    SCRIPTS_DIR / "consolidate_mermaid.py",
    SCRIPTS_DIR / "consolidate_templates.py",
    SCRIPTS_DIR / "consolidate_resources.py"
]

# Directory structure to ensure
DIRECTORIES = [
    SRC_DIR / "core",
    SRC_DIR / "prompt_manager",
    SRC_DIR / "mermaid",
    SRC_DIR / "templates",
    SRC_DIR / "prompts",
    SRC_DIR / "resources",
    SRC_DIR / "cli",
    SRC_DIR / "utils",
    PROJECT_ROOT / "tests" / "unit",
    PROJECT_ROOT / "tests" / "integration",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "config",
]


def ensure_directories():
    """Ensure all required directories exist."""
    print("Ensuring directory structure...")
    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  Created/ensured: {directory}")


def run_script(script_path: Path):
    """Run a Python script with proper error handling."""
    print(f"\nRunning script: {script_path}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running script {script_path}:")
        print(f"Exit code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def run_consolidation_scripts():
    """Run all consolidation scripts."""
    print("\nRunning consolidation scripts...")
    
    success = True
    for script in CONSOLIDATION_SCRIPTS:
        if not script.exists():
            print(f"Script not found: {script}")
            success = False
            continue
            
        if not run_script(script):
            success = False
    
    return success


def create_config_file():
    """Create a default configuration file."""
    print("\nCreating default configuration file...")
    
    config = {
        "name": "mcp-project-orchestrator",
        "version": "0.1.0",
        "description": "MCP Project Orchestrator Server",
        "server": {
            "host": "127.0.0.1",
            "port": 8080
        },
        "paths": {
            "prompts": str(SRC_DIR / "prompts"),
            "templates": str(SRC_DIR / "templates"),
            "resources": str(SRC_DIR / "resources"),
            "mermaid_templates": str(SRC_DIR / "mermaid" / "templates"),
            "mermaid_output": str(PROJECT_ROOT / "output" / "mermaid")
        },
        "logging": {
            "level": "INFO",
            "file": str(PROJECT_ROOT / "logs" / "orchestrator.log")
        },
        "mermaid": {
            "cli_path": "/usr/local/bin/mmdc"
        }
    }
    
    # Create logs and output directories
    (PROJECT_ROOT / "logs").mkdir(exist_ok=True)
    (PROJECT_ROOT / "output").mkdir(exist_ok=True)
    (PROJECT_ROOT / "output" / "mermaid").mkdir(exist_ok=True)
    
    # Save the config file
    config_path = PROJECT_ROOT / "config" / "default.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        
    print(f"  Created config file: {config_path}")
    return config_path


def create_init_files():
    """Create or update __init__.py files for all modules."""
    print("\nCreating __init__.py files for modules...")
    
    # Main package init
    with open(SRC_DIR / "__init__.py", 'w') as f:
        f.write('''"""
MCP Project Orchestrator - A comprehensive MCP server for project orchestration.

This package provides tools for project template management, prompt management,
and diagram generation through the Model Context Protocol (MCP).
"""

__version__ = "0.1.0"

from .core import FastMCPServer, MCPConfig, setup_logging, MCPException
from .prompt_manager import PromptManager, PromptTemplate, PromptLoader
from .mermaid import MermaidGenerator, MermaidRenderer, DiagramType

__all__ = [
    "FastMCPServer",
    "MCPConfig",
    "setup_logging",
    "MCPException",
    "PromptManager",
    "PromptTemplate",
    "PromptLoader",
    "MermaidGenerator",
    "MermaidRenderer",
    "DiagramType",
]
''')
    
    # Core module init
    with open(SRC_DIR / "core" / "__init__.py", 'w') as f:
        f.write('''"""
Core functionality for the MCP Project Orchestrator.

This module provides the core server and configuration components.
"""

from .fastmcp import FastMCPServer
from .config import MCPConfig
from .logging import setup_logging
from .exceptions import MCPException

__all__ = [
    "FastMCPServer",
    "MCPConfig",
    "setup_logging",
    "MCPException",
]
''')
    
    # Prompt manager module init
    with open(SRC_DIR / "prompt_manager" / "__init__.py", 'w') as f:
        f.write('''"""
Prompt management for the MCP Project Orchestrator.

This module provides template management and rendering capabilities.
"""

from .manager import PromptManager
from .template import PromptTemplate
from .loader import PromptLoader

__all__ = [
    "PromptManager",
    "PromptTemplate",
    "PromptLoader",
]
''')
    
    # Mermaid module init
    with open(SRC_DIR / "mermaid" / "__init__.py", 'w') as f:
        f.write('''"""
Mermaid diagram generation for the MCP Project Orchestrator.

This module provides diagram generation and rendering capabilities.
"""

from .generator import MermaidGenerator
from .renderer import MermaidRenderer
from .types import DiagramType

__all__ = [
    "MermaidGenerator",
    "MermaidRenderer",
    "DiagramType",
]
''')
    
    # Templates module init
    with open(SRC_DIR / "templates" / "__init__.py", 'w') as f:
        f.write('''"""
Project and component templates for the MCP Project Orchestrator.

This module provides template management and generation capabilities.
"""

from .project_templates import ProjectTemplateManager
from .component_templates import ComponentTemplateManager

__all__ = [
    "ProjectTemplateManager",
    "ComponentTemplateManager",
]
''')
    
    # Basic init files for other modules
    for module in ["prompts", "resources", "cli", "utils"]:
        with open(SRC_DIR / module / "__init__.py", 'w') as f:
            f.write(f'"""\n{module.capitalize()} module for the MCP Project Orchestrator.\n"""\n')
    
    print("  Created/updated all __init__.py files")


def create_entry_point():
    """Create a server entry point file."""
    print("\nCreating server entry point...")
    
    with open(SRC_DIR / "server.py", 'w') as f:
        f.write('''"""
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
''')
    
    # Create a CLI entry point
    with open(SRC_DIR / "__main__.py", 'w') as f:
        f.write('''"""
Command-line entry point for the MCP Project Orchestrator.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

from .server import start_server
from .core import MCPConfig, setup_logging


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Project Orchestrator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--log-level", help="Logging level")
    
    args = parser.parse_args()
    
    # Look for config file in standard locations
    config_path = args.config
    if not config_path:
        # Check common config locations
        config_locations = [
            Path.cwd() / "config" / "default.json",
            Path.home() / ".config" / "mcp-project-orchestrator" / "config.json",
            Path("/etc/mcp-project-orchestrator/config.json")
        ]
        
        for location in config_locations:
            if location.exists():
                config_path = str(location)
                break
    
    # Set up logging early
    logger = setup_logging(log_file=args.log_file)
    
    try:
        # Start the server
        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(start_server(config_path))
        
        # Run the server
        loop.run_forever()
    except KeyboardInterrupt:
        # Handle graceful shutdown
        logger.info("Shutting down server...")
        loop.run_until_complete(server.stop())
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)
    finally:
        loop.close()
    
    
if __name__ == "__main__":
    main()
''')

    print("  Created server entry point files")
    

def main():
    """Main function to orchestrate the setup process."""
    print("Setting up MCP Project Orchestrator...")
    
    # Ensure all directories exist
    ensure_directories()
    
    # Create init files
    create_init_files()
    
    # Create entry point
    create_entry_point()
    
    # Create default configuration
    config_path = create_config_file()
    
    # Run all consolidation scripts
    success = run_consolidation_scripts()
    
    if success:
        print("\nSetup completed successfully!")
        print(f"Configuration file: {config_path}")
        print("You can now run the server with:")
        print(f"  python -m mcp_project_orchestrator --config {config_path}")
    else:
        print("\nSetup completed with warnings or errors.")
        print("Please review the output above and fix any issues before running the server.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 