#!/usr/bin/env python3
"""
Conan recipe for MCP Project Orchestrator Complete Package.

This recipe packages the complete MCP Project Orchestrator ecosystem
with all dependencies and consumer applications.
"""

from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.python import PythonToolchain
import os

class MCPProjectOrchestratorCompleteConan(ConanFile):
    name = "mcp-project-orchestrator-complete"
    version = "0.2.0"
    description = "Complete MCP Project Orchestrator ecosystem with all dependencies and consumer applications"
    license = "MIT"
    url = "https://github.com/sparesparrow/mcp-project-orchestrator"
    homepage = "https://github.com/sparesparrow/mcp-project-orchestrator"
    topics = ("mcp", "orchestration", "agent-skills", "openssl", "fips", "complete-package")
    
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "include_openssl_tools": [True, False],
        "include_aws_sip_trunk": [True, False],
        "include_automotive_camera": [True, False],
        "include_printcast_agent": [True, False],
        "include_elevenlabs_agents": [True, False],
        "fips_enabled": [True, False],
        "aws_integration": [True, False],
        "cursor_integration": [True, False],
    }
    default_options = {
        "include_openssl_tools": True,
        "include_aws_sip_trunk": True,
        "include_automotive_camera": True,
        "include_printcast_agent": True,
        "include_elevenlabs_agents": True,
        "fips_enabled": True,
        "aws_integration": True,
        "cursor_integration": True,
    }
    
    exports_sources = "consumers/*", "templates/*", "configs/*", "scripts/*", "docs/*", "mcp/*", "*.py", "*.json", "*.md"
    
    def requirements(self):
        # Core MCP Project Orchestrator
        self.requires("mcp-project-orchestrator/0.2.0")
        
        # OpenSSL Tools and FIPS Compliance
        if self.options.include_openssl_tools:
            self.requires("openssl-tools-orchestrator/0.2.0")
            self.requires("openssl-fips-validator/0.2.0")
        
        # Agent Skills Framework
        self.requires("agent-skills-framework/0.2.0")
        
        # Consumer Applications
        if self.options.include_openssl_tools:
            self.requires("openssl-workflows/0.2.0")
        
        if self.options.include_aws_sip_trunk:
            self.requires("aws-sip-trunk/0.1.0")
        
        if self.options.include_automotive_camera:
            self.requires("automotive-camera-system/0.1.0")
        
        if self.options.include_printcast_agent:
            self.requires("printcast-agent/0.1.0")
        
        if self.options.include_elevenlabs_agents:
            self.requires("elevenlabs-agents/0.1.0")
        
        # Core Dependencies
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
        
        # Security and Cryptography
        self.requires("openssl/3.1.4")
        self.requires("zlib/1.3")
        
        if self.options.fips_enabled:
            self.requires("cryptography/41.0.7")
            self.requires("pycryptodome/3.19.0")
        
        # AWS Integration
        if self.options.aws_integration:
            self.requires("boto3/1.34.0")
            self.requires("botocore/1.34.0")
        
        # Development and Testing
        self.requires("pytest/7.4.3")
        self.requires("pytest-asyncio/0.21.1")
        self.requires("pytest-cov/4.1.0")
        self.requires("mypy/1.7.1")
        self.requires("ruff/0.1.6")
        
        # Build Tools
        self.requires("cmake/3.27.7")
        self.requires("ninja/1.11.1")
        
        # Optional Dependencies
        self.requires("numpy/1.25.2")
        self.requires("scikit-learn/1.3.2")
        self.requires("pandas/2.1.4")
        self.requires("redis/5.0.1")
        self.requires("memcached/1.6.21")
        self.requires("prometheus-client/0.19.0")
        self.requires("opentelemetry-api/1.21.0")
        self.requires("opentelemetry-sdk/1.21.0")
    
    def build_requirements(self):
        self.tool_requires("cmake/3.27.7")
        self.tool_requires("ninja/1.11.1")
    
    def generate(self):
        tc = PythonToolchain(self)
        tc.generate()
    
    def package(self):
        # Copy all consumers
        copy(self, "consumers/*", dst=os.path.join(self.package_folder, "consumers"), src=self.source_folder)
        
        # Copy templates
        copy(self, "templates/*", dst=os.path.join(self.package_folder, "templates"), src=self.source_folder)
        
        # Copy configurations
        copy(self, "configs/*", dst=os.path.join(self.package_folder, "configs"), src=self.source_folder)
        
        # Copy scripts
        copy(self, "scripts/*", dst=os.path.join(self.package_folder, "scripts"), src=self.source_folder)
        
        # Copy MCP components
        copy(self, "mcp/*", dst=os.path.join(self.package_folder, "mcp"), src=self.source_folder)
        
        # Copy documentation
        copy(self, "docs/*", dst=os.path.join(self.package_folder, "docs"), src=self.source_folder)
        
        # Copy Python files
        copy(self, "*.py", dst=os.path.join(self.package_folder, "src"), src=self.source_folder)
        
        # Copy JSON files
        copy(self, "*.json", dst=os.path.join(self.package_folder, "configs"), src=self.source_folder)
        
        # Copy markdown files
        copy(self, "*.md", dst=os.path.join(self.package_folder, "docs"), src=self.source_folder)
    
    def package_info(self):
        self.cpp_info.bindirs = ["consumers", "templates", "configs", "scripts", "mcp", "src", "docs"]
        
        # Python package info
        self.env_info.PYTHONPATH.append(os.path.join(self.package_folder, "src"))
        self.env_info.MCP_TEMPLATES_PATH = os.path.join(self.package_folder, "templates")
        self.env_info.MCP_CONFIGS_PATH = os.path.join(self.package_folder, "configs")
        self.env_info.MCP_SCRIPTS_PATH = os.path.join(self.package_folder, "scripts")
        self.env_info.MCP_CONSUMERS_PATH = os.path.join(self.package_folder, "consumers")
        
        # Feature-specific environment variables
        if self.options.fips_enabled:
            self.env_info.FIPS_ENABLED = "1"
        
        if self.options.aws_integration:
            self.env_info.AWS_INTEGRATION = "1"
        
        if self.options.cursor_integration:
            self.env_info.CURSOR_INTEGRATION = "1"
        
        # Consumer-specific environment variables
        if self.options.include_openssl_tools:
            self.env_info.OPENSSL_TOOLS_ENABLED = "1"
        
        if self.options.include_aws_sip_trunk:
            self.env_info.AWS_SIP_TRUNK_ENABLED = "1"
        
        if self.options.include_automotive_camera:
            self.env_info.AUTOMOTIVE_CAMERA_ENABLED = "1"
        
        if self.options.include_printcast_agent:
            self.env_info.PRINTCAST_AGENT_ENABLED = "1"
        
        if self.options.include_elevenlabs_agents:
            self.env_info.ELEVENLABS_AGENTS_ENABLED = "1"