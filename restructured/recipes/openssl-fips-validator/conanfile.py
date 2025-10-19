#!/usr/bin/env python3
"""
Conan recipe for OpenSSL FIPS Validator.

This recipe packages the FIPS compliance validation framework
for OpenSSL development with comprehensive security checks.
"""

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
import os

class OpenSSLFIPSValidatorConan(ConanFile):
    name = "openssl-fips-validator"
    version = "0.2.0"
    description = "FIPS 140-3 compliance validator for OpenSSL development"
    license = "MIT"
    url = "https://github.com/sparesparrow/openssl-fips-validator"
    homepage = "https://github.com/sparesparrow/openssl-fips-validator"
    topics = ("openssl", "fips", "compliance", "security", "validation", "cryptography")
    
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "fips_level": ["1", "2", "3", "4"],
        "enable_side_channel_analysis": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "fips_level": "1",
        "enable_side_channel_analysis": True,
    }
    
    exports_sources = "CMakeLists.txt", "src/*", "include/*", "tests/*", "docs/*"
    
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
    
    def requirements(self):
        self.requires("openssl/3.1.4")
        self.requires("zlib/1.3")
        self.requires("boost/1.83.0")
        self.requires("gtest/1.14.0")
        
        # FIPS-specific requirements
        if self.options.fips_level in ["2", "3", "4"]:
            self.requires("hardware-security-module/1.0.0")
        
        if self.options.enable_side_channel_analysis:
            self.requires("valgrind/3.20.0")
    
    def build_requirements(self):
        self.tool_requires("cmake/3.27.7")
        self.tool_requires("ninja/1.11.1")
        self.tool_requires("gtest/1.14.0")
    
    def layout(self):
        cmake_layout(self)
    
    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["FIPS_LEVEL"] = self.options.fips_level
        tc.variables["ENABLE_SIDE_CHANNEL_ANALYSIS"] = self.options.enable_side_channel_analysis
        tc.generate()
    
    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        
        # Run tests if not cross-compiling
        if not self.conf.get("tools.cmake.cross_building", default=False):
            cmake.test()
    
    def package(self):
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "include"))
        copy(self, "*.hpp", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "include"))
        copy(self, "*.lib", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.dll", dst=os.path.join(self.package_folder, "bin"), src=self.build_folder, keep_path=False)
        copy(self, "*.so", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.dylib", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.a", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        
        # Copy documentation
        copy(self, "docs/*", dst=os.path.join(self.package_folder, "docs"), src=self.source_folder)
    
    def package_info(self):
        self.cpp_info.libs = ["openssl_fips_validator"]
        self.cpp_info.defines = [f"FIPS_LEVEL={self.options.fips_level}"]
        
        if self.options.enable_side_channel_analysis:
            self.cpp_info.defines.append("ENABLE_SIDE_CHANNEL_ANALYSIS=1")
        
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread", "dl"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32", "crypt32"]
        
        # FIPS compliance information
        self.cpp_info.set_property("fips_compliant", True)
        self.cpp_info.set_property("fips_level", self.options.fips_level)
        self.cpp_info.set_property("security_validated", True)