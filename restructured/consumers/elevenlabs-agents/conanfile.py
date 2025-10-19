#!/usr/bin/env python3
"""
Conan recipe for ElevenLabs Agents.

This recipe packages ElevenLabs AI agents with
voice synthesis and natural language processing.
"""

from conan import ConanFile
from conan.tools.files import copy
import os

class ElevenLabsAgentsConan(ConanFile):
    name = "elevenlabs-agents"
    version = "0.1.0"
    description = "ElevenLabs AI agents with voice synthesis"
    license = "MIT"
    url = "https://github.com/sparesparrow/elevenlabs-agents"
    homepage = "https://github.com/sparesparrow/elevenlabs-agents"
    topics = ("elevenlabs", "ai", "voice", "synthesis", "agents")
    
    settings = "os", "arch"
    
    exports_sources = "*.json", "*.py", "*.md", "*.txt"
    
    def requirements(self):
        self.requires("python/3.11")
        self.requires("requests/2.31.0")
        self.requires("pydantic/2.5.0")
        self.requires("openai/1.3.0")
    
    def package(self):
        copy(self, "*.json", dst=os.path.join(self.package_folder, "config"), src=self.source_folder)
        copy(self, "*.py", dst=os.path.join(self.package_folder, "src"), src=self.source_folder)
        copy(self, "*.md", dst=os.path.join(self.package_folder, "docs"), src=self.source_folder)
        copy(self, "*.txt", dst=os.path.join(self.package_folder, "docs"), src=self.source_folder)
    
    def package_info(self):
        self.cpp_info.bindirs = ["config", "src", "docs"]
