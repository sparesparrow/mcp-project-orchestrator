#!/usr/bin/env python3
"""
Conan recipe for Automotive Camera System.

This recipe packages the automotive camera system with
computer vision and real-time processing capabilities.
"""

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy
import os

class AutomotiveCameraConan(ConanFile):
    name = "automotive-camera-system"
    version = "0.1.0"
    description = "Automotive camera system with computer vision"
    license = "MIT"
    url = "https://github.com/sparesparrow/automotive-camera-system"
    homepage = "https://github.com/sparesparrow/automotive-camera-system"
    topics = ("automotive", "camera", "computer-vision", "real-time")
    
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    
    exports_sources = "CMakeLists.txt", "src/*", "include/*", "docs/*"
    
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
    
    def requirements(self):
        self.requires("opencv/4.8.0")
        self.requires("eigen/3.4.0")
        self.requires("gstreamer/1.22.0")
        self.requires("gst-plugins-base/1.22.0")
    
    def build_requirements(self):
        self.tool_requires("cmake/3.27.7")
        self.tool_requires("ninja/1.11.1")
    
    def layout(self):
        cmake_layout(self)
    
    def generate(self):
        tc = CMakeToolchain(self)
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
        self.cpp_info.libs = ["automotive_camera"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
