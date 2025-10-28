"""
Platform detection utilities for Cursor configuration deployment.

This module detects the developer's platform and environment to select
appropriate rule templates and configuration settings.
"""

import platform
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class PlatformDetector:
    """Detect developer platform and environment for Cursor configuration."""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def detect_platform(self) -> Dict[str, Any]:
        """
        Detect developer platform and environment.
        
        Returns:
            Dictionary containing platform information including OS, 
            version, Python version, CI status, and user details.
        """
        if self._cache:
            return self._cache
        
        system = platform.system().lower()
        
        # Detect CI environment
        is_ci = os.getenv("CI", "false").lower() == "true"
        is_github_actions = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
        is_gitlab_ci = os.getenv("GITLAB_CI", "false").lower() == "true"
        is_jenkins = os.getenv("JENKINS_URL") is not None
        
        # Get user information
        user = os.getenv("USER", os.getenv("USERNAME", "developer"))
        home = str(Path.home())
        
        # Detect shell
        shell = os.getenv("SHELL", "/bin/bash")
        if system == "windows":
            shell = os.getenv("COMSPEC", "cmd.exe")
        
        # Detect development tools
        has_git = self._has_command("git")
        has_conan = self._has_command("conan")
        has_cursor = self._has_command("cursor")
        
        # Detect Python environment
        python_version = platform.python_version()
        python_implementation = platform.python_implementation()
        
        # Detect if running in virtual environment
        in_venv = (
            hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.getenv("VIRTUAL_ENV") is not None
        )
        
        platform_info = {
            "os": system,
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": python_version,
            "python_implementation": python_implementation,
            "in_venv": in_venv,
            "is_ci": is_ci,
            "is_github_actions": is_github_actions,
            "is_gitlab_ci": is_gitlab_ci,
            "is_jenkins": is_jenkins,
            "user": user,
            "home": home,
            "shell": shell,
            "has_git": has_git,
            "has_conan": has_conan,
            "has_cursor": has_cursor,
            "timestamp": datetime.now().isoformat(),
        }
        
        self._cache = platform_info
        return platform_info
    
    def _has_command(self, command: str) -> bool:
        """Check if a command is available in PATH."""
        import shutil
        return shutil.which(command) is not None
    
    def get_rule_template_name(self) -> str:
        """
        Get the appropriate rule template name based on platform detection.
        
        Returns:
            Template filename (without .jinja2 extension)
        """
        platform_info = self.detect_platform()
        
        if platform_info["is_ci"]:
            return "ci-linux"  # Default CI template
        else:
            os_name = platform_info["os"]
            return f"{os_name}-dev"
    
    def get_mcp_command(self) -> str:
        """
        Get the appropriate MCP command for the platform.
        
        Returns:
            Command to run MCP servers (npx or npx.cmd)
        """
        platform_info = self.detect_platform()
        
        if platform_info["os"] == "windows":
            return "npx.cmd"
        else:
            return "npx"
    
    def is_development_environment(self) -> bool:
        """Check if this is a development environment (not CI)."""
        platform_info = self.detect_platform()
        return not platform_info["is_ci"]
    
    def get_conan_home(self) -> str:
        """Get the Conan home directory for this platform."""
        platform_info = self.detect_platform()
        conan_home = os.getenv("CONAN_USER_HOME")
        
        if conan_home:
            return conan_home
        
        # Default Conan home
        home = platform_info["home"]
        if platform_info["os"] == "windows":
            return f"{home}\\.conan2"
        else:
            return f"{home}/.conan2"


# Import sys for virtual environment detection
import sys