"""
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
