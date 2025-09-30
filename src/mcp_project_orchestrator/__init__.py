"""
MCP Project Orchestrator - A comprehensive MCP server for project orchestration.

This package provides tools for project template management, prompt management,
diagram generation, and AWS integration through the Model Context Protocol (MCP).
"""

__version__ = "0.1.0"

from .core import FastMCPServer, MCPConfig, setup_logging, MCPException
from .prompt_manager import PromptManager, PromptTemplate, PromptLoader
from .mermaid import MermaidGenerator, MermaidRenderer, DiagramType

# AWS MCP integration (optional)
try:
    from .aws_mcp import AWSConfig, AWSMCPIntegration, register_aws_mcp_tools
    _AWS_AVAILABLE = True
except ImportError:
    _AWS_AVAILABLE = False
    AWSConfig = None
    AWSMCPIntegration = None
    register_aws_mcp_tools = None

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

# Add AWS exports if available
if _AWS_AVAILABLE:
    __all__.extend([
        "AWSConfig",
        "AWSMCPIntegration",
        "register_aws_mcp_tools",
    ])
