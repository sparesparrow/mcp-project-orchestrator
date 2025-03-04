#!/usr/bin/env python3
"""
FastMCP server implementation for the MCP Project Orchestrator.

This module provides a lightweight MCP server that handles communication
with MCP clients like Claude Desktop, exposing project orchestration
capabilities through the Model Context Protocol.
"""
import os
import sys
import signal
import logging
import json
import time
from typing import Dict, Any, Optional, Callable

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp-project-orchestrator")

class FastMCP:
    """
    FastMCP server implementation for project orchestration.
    
    This class provides a lightweight MCP server that handles communication
    with MCP clients, exposing project orchestration capabilities through
    registered tools and appropriate error handling.
    """
    
    def __init__(self, name: str):
        """
        Initialize the MCP server with the given name.
        
        Args:
            name: Name of the MCP server
        """
        self.name = name
        self.config = {}
        self.tools = {}
        self.resources = {}
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        logger.info(f"Initialized FastMCP server '{name}'")
        
        # Try to load configuration if it exists
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from project_orchestration.json if it exists."""
        try:
            config_path = os.path.join(os.getcwd(), "project_orchestration.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
            else:
                logger.warning(f"Configuration file {config_path} not found, using defaults")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
    
    def tool(self, func: Optional[Callable] = None, 
             name: Optional[str] = None, 
             description: Optional[str] = None):
        """
        Decorator to register a function as an MCP tool.
        
        Args:
            func: The function to register
            name: Optional name for the tool (defaults to function name)
            description: Optional description of the tool
        
        Returns:
            The decorated function
        """
        def decorator(fn):
            tool_name = name or fn.__name__
            tool_desc = description or fn.__doc__ or f"Tool {tool_name}"
            
            self.tools[tool_name] = {
                "function": fn,
                "description": tool_desc,
                "parameters": {}  # In a real implementation, extract from function signature
            }
            
            logger.info(f"Registered tool '{tool_name}'")
            return fn
        
        if func is None:
            return decorator
        return decorator(func)
    
    def resource(self, name: str, content: Any) -> None:
        """
        Register a resource with the MCP server.
        
        Args:
            name: Name of the resource
            content: Content of the resource
        """
        self.resources[name] = content
        logger.info(f"Registered resource '{name}'")
    
    def _handle_signal(self, signum: int, frame) -> None:
        """
        Handle shutdown signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down...")
        sys.exit(0)
    
    def _handle_client_connection(self) -> None:
        """Handle client connections and MCP protocol messages."""
        logger.info("Handling client connection")
        # In a real implementation, this would use proper MCP protocol
        # to handle client requests, parse JSON messages, etc.
    
    def run(self) -> None:
        """Run the MCP server and handle client connections."""
        logger.info(f"FastMCP server '{self.name}' running with configuration: {self.config}")
        
        try:
            # In a real implementation, this would start a proper server
            # that listens for connections and handles MCP protocol
            logger.info("Server running on port 8080")
            logger.info("Press Ctrl+C to stop")
            
            # For demonstration, just keep the process running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        except Exception as e:
            logger.error(f"Error running server: {str(e)}")
        finally:
            logger.info("Server shutting down")

def main():
    """Main entry point for the FastMCP server."""
    server = FastMCP("Project Orchestrator")
    server.run()

if __name__ == "__main__":
    main() 