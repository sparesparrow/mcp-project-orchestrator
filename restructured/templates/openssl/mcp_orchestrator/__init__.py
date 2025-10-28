"""
MCP Project Orchestrator for OpenSSL

This package provides Cursor configuration management for OpenSSL development,
similar to how Conan manages build profiles.
"""

__version__ = "0.1.0"
__author__ = "MCP Project Orchestrator Team"

from .cursor_deployer import CursorConfigDeployer
from .cursor_config import CursorConfig
from .platform_detector import PlatformDetector

__all__ = [
    "CursorConfigDeployer",
    "CursorConfig", 
    "PlatformDetector",
]