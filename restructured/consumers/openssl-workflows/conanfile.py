#!/usr/bin/env python3
"""
Conan recipe for OpenSSL Workflows.

This recipe packages GitHub Actions workflows for OpenSSL development
with CI/CD automation and FIPS compliance validation.
"""

from conan import ConanFile
from conan.tools.files import copy
import os

class OpenSSLWorkflowsConan(ConanFile):
    name = "openssl-workflows"
    version = "0.2.0"
    description = "GitHub Actions workflows for OpenSSL development"
    license = "MIT"
    url = "https://github.com/sparesparrow/openssl-workflows"
    homepage = "https://github.com/sparesparrow/openssl-workflows"
    topics = ("openssl", "github-actions", "ci-cd", "fips", "workflows")
    
    settings = "os", "arch"
    
    exports_sources = "*.yml", "*.yaml", "scripts/*", "templates/*"
    
    def package(self):
        copy(self, "*.yml", dst=os.path.join(self.package_folder, "workflows"), src=self.source_folder)
        copy(self, "*.yaml", dst=os.path.join(self.package_folder, "workflows"), src=self.source_folder)
        copy(self, "scripts/*", dst=os.path.join(self.package_folder, "scripts"), src=self.source_folder)
        copy(self, "templates/*", dst=os.path.join(self.package_folder, "templates"), src=self.source_folder)
    
    def package_info(self):
        self.cpp_info.bindirs = ["workflows", "scripts", "templates"]
