from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.files import copy


class OpenSSLExampleConan(ConanFile):
    name = "openssl-example"
    version = "1.0.0"
    description = "Example OpenSSL project with Cursor AI configuration"
    license = "MIT"
    url = "https://github.com/sparesparrow/openssl-example"
    homepage = "https://github.com/sparesparrow/openssl-example"
    topics = ("openssl", "cryptography", "cursor", "ai")
    
    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
    }
    
    # Sources are located in the same place as this recipe, copy them to the recipe
    exports_sources = "CMakeLists.txt", "src/*"
    
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
    
    def layout(self):
        cmake_layout(self)
    
    def requirements(self):
        self.requires("openssl/3.1.0")
        self.requires("zlib/1.2.13")
    
    def build_requirements(self):
        self.tool_requires("cmake/[>=3.15]")
    
    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
    
    def package(self):
        cmake = CMake(self)
        cmake.install()
        
        # Copy additional files
        copy(self, "*.h", src=self.source_folder, dst=self.package_folder)
    
    def package_info(self):
        self.cpp_info.libs = ["openssl_example"]
        
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]