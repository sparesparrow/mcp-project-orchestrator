#!/usr/bin/env python3
"""
Conan recipe for Printcast Agent.

This recipe packages the Printcast Agent with
Docker containerization and web interface.
"""

from conan import ConanFile
from conan.tools.files import copy
import os

class PrintcastAgentConan(ConanFile):
    name = "printcast-agent"
    version = "0.1.0"
    description = "Printcast Agent with Docker and web interface"
    license = "MIT"
    url = "https://github.com/sparesparrow/printcast-agent"
    homepage = "https://github.com/sparesparrow/printcast-agent"
    topics = ("printcast", "agent", "docker", "web", "printing")
    
    settings = "os", "arch"
    
    exports_sources = "src/*", "tests/*", "scripts/*", "config/*", "*.py", "*.yml", "*.yaml"
    
    def requirements(self):
        self.requires("python/3.11")
        self.requires("fastapi/0.104.1")
        self.requires("uvicorn/0.24.0")
        self.requires("pydantic/2.5.0")
        self.requires("docker/6.1.3")
    
    def package(self):
        copy(self, "src/*", dst=os.path.join(self.package_folder, "src"), src=self.source_folder)
        copy(self, "tests/*", dst=os.path.join(self.package_folder, "tests"), src=self.source_folder)
        copy(self, "scripts/*", dst=os.path.join(self.package_folder, "scripts"), src=self.source_folder)
        copy(self, "config/*", dst=os.path.join(self.package_folder, "config"), src=self.source_folder)
        copy(self, "*.py", dst=os.path.join(self.package_folder, "src"), src=self.source_folder)
        copy(self, "*.yml", dst=os.path.join(self.package_folder, "docker"), src=self.source_folder)
        copy(self, "*.yaml", dst=os.path.join(self.package_folder, "docker"), src=self.source_folder)
    
    def package_info(self):
        self.cpp_info.bindirs = ["src", "tests", "scripts", "config", "docker"]
