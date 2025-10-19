#!/usr/bin/env python3
"""
Conan recipe for MCP Project Orchestrator.

This recipe packages the core MCP Project Orchestrator with
Agent Skills integration and comprehensive project management capabilities.
"""

from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.python import PythonToolchain, PythonRequire
import os

class MCPProjectOrchestratorConan(ConanFile):
    name = "mcp-project-orchestrator"
    version = "0.2.0"
    description = "MCP Project Orchestrator with Agent Skills Integration"
    license = "MIT"
    url = "https://github.com/sparesparrow/mcp-project-orchestrator"
    homepage = "https://github.com/sparesparrow/mcp-project-orchestrator"
    topics = ("mcp", "orchestration", "agent-skills", "project-management", "automation")
    
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fips_enabled": [True, False],
        "aws_integration": [True, False],
        "cursor_integration": [True, False],
    }
    default_options = {
        "fips_enabled": True,
        "aws_integration": True,
        "cursor_integration": True,
    }
    
    exports_sources = "src/*", "templates/*", "configs/*", "scripts/*", "docs/*", "*.py", "*.json", "*.md"
    
    def requirements(self):
        self.requires("python/3.11")
        self.requires("fastapi/0.104.1")
        self.requires("uvicorn/0.24.0")
        self.requires("pydantic/2.5.0")
        self.requires("jinja2/3.1.2")
        self.requires("pyyaml/6.0.1")
        self.requires("rich/13.7.0")
        self.requires("typer/0.9.0")
        self.requires("httpx/0.25.2")
        self.requires("aiofiles/23.2.1")
        
        if self.options.fips_enabled:
            self.requires("cryptography/41.0.7")
            self.requires("pycryptodome/3.19.0")
        
        if self.options.aws_integration:
            self.requires("boto3/1.34.0")
            self.requires("botocore/1.34.0")
        
        if self.options.cursor_integration:
            self.requires("pydantic-settings/2.1.0")
            self.requires("click/8.1.7")
    
    def build_requirements(self):
        self.tool_requires("pytest/7.4.3")
        self.tool_requires("pytest-asyncio/0.21.1")
        self.tool_requires("pytest-cov/4.1.0")
        self.tool_requires("mypy/1.7.1")
        self.tool_requires("ruff/0.1.6")
    
    def generate(self):
        tc = PythonToolchain(self)
        tc.generate()
    
    def package(self):
        # Copy Python source files
        copy(self, "src/*", dst=os.path.join(self.package_folder, "src"), src=self.source_folder)
        
        # Copy templates
        copy(self, "templates/*", dst=os.path.join(self.package_folder, "templates"), src=self.source_folder)
        
        # Copy configurations
        copy(self, "configs/*", dst=os.path.join(self.package_folder, "configs"), src=self.source_folder)
        
        # Copy scripts
        copy(self, "scripts/*", dst=os.path.join(self.package_folder, "scripts"), src=self.source_folder)
        
        # Copy documentation
        copy(self, "docs/*", dst=os.path.join(self.package_folder, "docs"), src=self.source_folder)
        
        # Copy Python files
        copy(self, "*.py", dst=os.path.join(self.package_folder, "src"), src=self.source_folder)
        
        # Copy JSON files
        copy(self, "*.json", dst=os.path.join(self.package_folder, "configs"), src=self.source_folder)
        
        # Copy markdown files
        copy(self, "*.md", dst=os.path.join(self.package_folder, "docs"), src=self.source_folder)
    
    def package_info(self):
        self.cpp_info.bindirs = ["src", "templates", "configs", "scripts", "docs"]
        
        # Python package info
        self.env_info.PYTHONPATH.append(os.path.join(self.package_folder, "src"))
        self.env_info.MCP_TEMPLATES_PATH = os.path.join(self.package_folder, "templates")
        self.env_info.MCP_CONFIGS_PATH = os.path.join(self.package_folder, "configs")
        self.env_info.MCP_SCRIPTS_PATH = os.path.join(self.package_folder, "scripts")
        
        # Feature-specific environment variables
        if self.options.fips_enabled:
            self.env_info.FIPS_ENABLED = "1"
        
        if self.options.aws_integration:
            self.env_info.AWS_INTEGRATION = "1"
        
        if self.options.cursor_integration:
            self.env_info.CURSOR_INTEGRATION = "1"