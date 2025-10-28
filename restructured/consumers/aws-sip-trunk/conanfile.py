#!/usr/bin/env python3
"""
Conan recipe for AWS SIP Trunk.

This recipe packages the AWS SIP Trunk deployment system with
Asterisk configuration and Terraform infrastructure.
"""

from conan import ConanFile
from conan.tools.files import copy
import os

class AWSSIPTrunkConan(ConanFile):
    name = "aws-sip-trunk"
    version = "0.1.0"
    description = "AWS SIP Trunk deployment with Asterisk and Terraform"
    license = "MIT"
    url = "https://github.com/sparesparrow/aws-sip-trunk"
    homepage = "https://github.com/sparesparrow/aws-sip-trunk"
    topics = ("aws", "sip", "asterisk", "terraform", "voip")
    
    settings = "os", "arch"
    
    exports_sources = "terraform/*", "config/*", "scripts/*", "tests/*", "*.py"
    
    def requirements(self):
        self.requires("terraform/1.6.0")
        self.requires("python/3.11")
    
    def package(self):
        copy(self, "terraform/*", dst=os.path.join(self.package_folder, "terraform"), src=self.source_folder)
        copy(self, "config/*", dst=os.path.join(self.package_folder, "config"), src=self.source_folder)
        copy(self, "scripts/*", dst=os.path.join(self.package_folder, "scripts"), src=self.source_folder)
        copy(self, "tests/*", dst=os.path.join(self.package_folder, "tests"), src=self.source_folder)
        copy(self, "*.py", dst=os.path.join(self.package_folder, "src"), src=self.source_folder)
    
    def package_info(self):
        self.cpp_info.bindirs = ["terraform", "config", "scripts", "tests", "src"]
