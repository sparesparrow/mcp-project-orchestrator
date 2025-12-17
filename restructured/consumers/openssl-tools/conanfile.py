#!/usr/bin/env python3
"""
Conan recipe for OpenSSL Tools Orchestration.

This recipe packages the OpenSSL Tools orchestration system with
Agent Skills integration and FIPS compliance capabilities.
"""

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
import os

class OpenSSLToolsConan(ConanFile):
    name = "openssl-tools-orchestrator"
    version = "0.2.0"
    description = "OpenSSL Tools Orchestration with Agent Skills Integration"
    license = "MIT"
    url = "https://github.com/sparesparrow/openssl-tools"
    homepage = "https://github.com/sparesparrow/openssl-tools"
    topics = ("openssl", "fips", "orchestration", "mcp", "agent-skills")
    
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "fips_enabled": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "fips_enabled": True,
        "shared": False,
        "fPIC": True,
    }
    
    exports_sources = "CMakeLists.txt", "src/*", "include/*", "tests/*"
    
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
    
    def requirements(self):
        self.requires("openssl/3.1.4")
        self.requires("zlib/1.3")
        self.requires("cmake/3.27.7")
        self.requires("ninja/1.11.1")
        
        if self.options.fips_enabled:
            self.requires("fips-crypto/1.0.0")
    
    def build_requirements(self):
        self.tool_requires("cmake/3.27.7")
        self.tool_requires("ninja/1.11.1")
    
    def layout(self):
        cmake_layout(self)
    
    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["FIPS_ENABLED"] = self.options.fips_enabled
        tc.generate()
    
    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
    
    def package(self):
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "include"))
        copy(self, "*.lib", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.dll", dst=os.path.join(self.package_folder, "bin"), src=self.build_folder, keep_path=False)
        copy(self, "*.so", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.dylib", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.a", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
    
    def package_info(self):
        self.cpp_info.libs = ["openssl_tools_orchestrator"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        if self.options.fips_enabled:
            self.cpp_info.defines = ["FIPS_MODE=1"]
