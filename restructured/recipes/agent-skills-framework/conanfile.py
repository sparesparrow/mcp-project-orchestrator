#!/usr/bin/env python3
"""
Conan recipe for Agent Skills Framework.

This recipe packages the Agent Skills framework with
progressive disclosure and dynamic composition capabilities.
"""

from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.python import PythonToolchain
import os

class AgentSkillsFrameworkConan(ConanFile):
    name = "agent-skills-framework"
    version = "0.2.0"
    description = "Agent Skills framework with progressive disclosure and dynamic composition"
    license = "MIT"
    url = "https://github.com/sparesparrow/agent-skills-framework"
    homepage = "https://github.com/sparesparrow/agent-skills-framework"
    topics = ("agent-skills", "ai", "orchestration", "progressive-disclosure", "composition")
    
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "enable_ml_optimization": [True, False],
        "enable_caching": [True, False],
        "enable_monitoring": [True, False],
    }
    default_options = {
        "enable_ml_optimization": True,
        "enable_caching": True,
        "enable_monitoring": True,
    }
    
    exports_sources = "src/*", "templates/*", "configs/*", "scripts/*", "docs/*", "*.py", "*.json", "*.md"
    
    def requirements(self):
        self.requires("python/3.11")
        self.requires("pydantic/2.5.0")
        self.requires("typing-extensions/4.8.0")
        self.requires("aiofiles/23.2.1")
        self.requires("httpx/0.25.2")
        self.requires("jinja2/3.1.2")
        self.requires("pyyaml/6.0.1")
        self.requires("rich/13.7.0")
        self.requires("click/8.1.7")
        
        if self.options.enable_ml_optimization:
            self.requires("numpy/1.25.2")
            self.requires("scikit-learn/1.3.2")
            self.requires("pandas/2.1.4")
        
        if self.options.enable_caching:
            self.requires("redis/5.0.1")
            self.requires("memcached/1.6.21")
        
        if self.options.enable_monitoring:
            self.requires("prometheus-client/0.19.0")
            self.requires("opentelemetry-api/1.21.0")
            self.requires("opentelemetry-sdk/1.21.0")
    
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
        self.env_info.AGENT_SKILLS_TEMPLATES_PATH = os.path.join(self.package_folder, "templates")
        self.env_info.AGENT_SKILLS_CONFIGS_PATH = os.path.join(self.package_folder, "configs")
        self.env_info.AGENT_SKILLS_SCRIPTS_PATH = os.path.join(self.package_folder, "scripts")
        
        # Feature-specific environment variables
        if self.options.enable_ml_optimization:
            self.env_info.AGENT_SKILLS_ML_OPTIMIZATION = "1"
        
        if self.options.enable_caching:
            self.env_info.AGENT_SKILLS_CACHING = "1"
        
        if self.options.enable_monitoring:
            self.env_info.AGENT_SKILLS_MONITORING = "1"