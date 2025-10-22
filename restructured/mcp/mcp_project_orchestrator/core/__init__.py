"""
Core functionality for the MCP Project Orchestrator.

This module provides the core server and configuration components.
"""

from .fastmcp import FastMCPServer
from .config import MCPConfig
from .logging import setup_logging
from .exceptions import MCPException, ErrorCode
from .base import BaseComponent, BaseTemplate, BaseManager, BaseOrchestrator
from .managers import BaseResourceManager

# Provide Config as an alias for backward compatibility
Config = MCPConfig

__all__ = [
    "FastMCPServer",
    "MCPConfig",
    "Config",  # Alias for backward compatibility
    "setup_logging",
    "MCPException",
    "ErrorCode",
    "BaseComponent",
    "BaseTemplate", 
    "BaseManager",
    "BaseOrchestrator",
    "BaseResourceManager",
] 