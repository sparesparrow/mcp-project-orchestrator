"""
MCP Project Orchestrator with Agent Skills Integration.

This package provides comprehensive project orchestration capabilities with
Agent Skills integration, MCP 2025 protocol support, and specialized tools
for OpenSSL development and FIPS compliance.
"""

from .fastmcp import FastMCP
from .project_orchestration import mcp
from .skills_registry import (
    SkillsRegistry,
    ProjectContext,
    SkillComposition,
    SkillMetadata,
    SkillType,
    SkillPriority
)
from .skills_enabled_mcp import SkillsEnabledMCPServer
from .fips_compliance import (
    FIPSComplianceValidator,
    FIPSValidationLevel,
    SecurityViolation,
    SecurityViolationType
)
from .cursor_integration import (
    CursorCLIManager,
    CursorAgentOrchestrator,
    CursorExecutionMode
)
from .openssl_tools_orchestration import (
    OpenSSLToolsOrchestrator,
    OpenSSLProjectContext,
    OpenSSLProjectType,
    BuildPlatform,
    WorkflowTrigger
)
from .openssl_orchestration_main import OpenSSLOrchestrationMain

__version__ = "0.2.0"
__author__ = "sparesparrow"
__description__ = "MCP Project Orchestrator with Agent Skills Integration"

# Export main classes and functions
__all__ = [
    # Core MCP functionality
    "FastMCP",
    "mcp",
    
    # Skills registry and composition
    "SkillsRegistry",
    "ProjectContext", 
    "SkillComposition",
    "SkillMetadata",
    "SkillType",
    "SkillPriority",
    
    # Enhanced MCP server
    "SkillsEnabledMCPServer",
    
    # FIPS compliance
    "FIPSComplianceValidator",
    "FIPSValidationLevel",
    "SecurityViolation",
    "SecurityViolationType",
    
    # Cursor integration
    "CursorCLIManager",
    "CursorAgentOrchestrator",
    "CursorExecutionMode",
    
    # OpenSSL orchestration
    "OpenSSLToolsOrchestrator",
    "OpenSSLProjectContext",
    "OpenSSLProjectType",
    "BuildPlatform",
    "WorkflowTrigger",
    
    # Main orchestration entry point
    "OpenSSLOrchestrationMain"
]