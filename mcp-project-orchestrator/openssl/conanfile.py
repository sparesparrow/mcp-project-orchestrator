"""
Conan package for mcp-project-orchestrator/openssl

This package provides Cursor configuration management for OpenSSL development,
similar to how Conan manages build profiles.
"""

from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
import os


class MCPProjectOrchestratorOpenSSLConan(ConanFile):
    name = "mcp-project-orchestrator-openssl"
    version = "0.1.0"
    description = "Cursor configuration management for OpenSSL development"
    license = "MIT"
    url = "https://github.com/sparesparrow/mcp-project-orchestrator"
    homepage = "https://github.com/sparesparrow/mcp-project-orchestrator"
    topics = ("openssl", "cursor", "ide", "configuration", "management", "conan", "build", "profiles")
    package_type = "python-require"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_cursor": [True, False],
        "cursor_opt_out": [True, False],
    }
    default_options = {
        "with_cursor": True,
        "cursor_opt_out": False,
    }
    
    def configure(self):
        """Configure the package."""
        # This is a Python package, not a C++ library
        self.settings.rm_safe("compiler")
        self.settings.rm_safe("build_type")
        self.settings.rm_safe("arch")
    
    def layout(self):
        """Set up the package layout."""
        basic_layout(self)
    
    def requirements(self):
        """Define package requirements."""
        self.requires("python_requires/click/8.0.0")
        self.requires("python_requires/jinja2/3.0.0")
    
    def build_requirements(self):
        """Define build requirements."""
        if self.options.with_cursor:
            self.build_requires("python_requires/click/8.0.0")
            self.build_requires("python_requires/jinja2/3.0.0")
    
    def source(self):
        """Download source code."""
        # This package contains only Python code and templates
        # No external source download needed
        pass
    
    def build(self):
        """Build the package."""
        # This is a Python package, no compilation needed
        pass
    
    def package(self):
        """Package the files."""
        # Copy Python package
        copy(self, "mcp_orchestrator/*", src=self.source_folder, dst=os.path.join(self.package_folder, "mcp_orchestrator"))
        
        # Copy cursor-rules templates
        copy(self, "cursor-rules/**/*", src=self.source_folder, dst=os.path.join(self.package_folder, "cursor-rules"))
        
        # Copy configuration files
        copy(self, "pyproject.toml", src=self.source_folder, dst=self.package_folder)
        copy(self, "setup.py", src=self.source_folder, dst=self.package_folder)
        copy(self, "requirements.txt", src=self.source_folder, dst=self.package_folder)
    
    def package_info(self):
        """Define package information."""
        # Set Python path
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        
        # Set Python package path
        self.env_info.PYTHONPATH.append(os.path.join(self.package_folder, "mcp_orchestrator"))
        
        # Set cursor-rules path
        self.env_info.CURSOR_RULES_PATH = os.path.join(self.package_folder, "cursor-rules")
        
        # Set package options
        self.env_info.MCP_ORCHESTRATOR_WITH_CURSOR = str(self.options.with_cursor)
        self.env_info.MCP_ORCHESTRATOR_CURSOR_OPT_OUT = str(self.options.cursor_opt_out)
    
    def deploy(self):
        """Deploy the package."""
        # Copy Python package to destination
        copy(self, "mcp_orchestrator/*", src=self.package_folder, dst=self.build_folder)
        
        # Copy cursor-rules templates
        copy(self, "cursor-rules/**/*", src=self.package_folder, dst=self.build_folder)
        
        # Copy configuration files
        copy(self, "pyproject.toml", src=self.package_folder, dst=self.build_folder)
        copy(self, "setup.py", src=self.package_folder, dst=self.build_folder)
        copy(self, "requirements.txt", src=self.package_folder, dst=self.build_folder)
    
    def package_id(self):
        """Customize package ID."""
        # Include options in package ID
        self.info.options.with_cursor = self.options.with_cursor
        self.info.options.cursor_opt_out = self.options.cursor_opt_out