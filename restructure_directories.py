#!/usr/bin/env python3
"""
Directory Restructuring Script for MCP Project Orchestrator.

This script restructures the project directory by type and consumers,
and creates Conan recipes for repositories without conanfile.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DirectoryType(Enum):
    """Types of directories for organization."""
    TEMPLATES = "templates"
    SCRIPTS = "scripts"
    CONFIGS = "configs"
    RECIPES = "recipes"
    DOCS = "docs"
    MCP = "mcp"
    CONSUMERS = "consumers"

class ConsumerType(Enum):
    """Types of consumers."""
    OPENSSL_TOOLS = "openssl-tools"
    OPENSSL_WORKFLOWS = "openssl-workflows"
    AWS_SIP_TRUNK = "aws-sip-trunk"
    AUTOMOTIVE_CAMERA = "automotive-camera"
    PRINTCAST_AGENT = "printcast-agent"
    ELEVENLABS_AGENTS = "elevenlabs-agents"

@dataclass
class DirectoryStructure:
    """Defines the new directory structure."""
    base_path: Path
    types: Dict[DirectoryType, Path]
    consumers: Dict[ConsumerType, Path]

def create_directory_structure(base_path: Path) -> DirectoryStructure:
    """Create the new directory structure."""
    
    # Base directories by type
    types = {
        DirectoryType.TEMPLATES: base_path / "templates",
        DirectoryType.SCRIPTS: base_path / "scripts", 
        DirectoryType.CONFIGS: base_path / "configs",
        DirectoryType.RECIPES: base_path / "recipes",
        DirectoryType.DOCS: base_path / "docs",
        DirectoryType.MCP: base_path / "mcp",
        DirectoryType.CONSUMERS: base_path / "consumers"
    }
    
    # Consumer-specific directories
    consumers = {
        ConsumerType.OPENSSL_TOOLS: base_path / "consumers" / "openssl-tools",
        ConsumerType.OPENSSL_WORKFLOWS: base_path / "consumers" / "openssl-workflows", 
        ConsumerType.AWS_SIP_TRUNK: base_path / "consumers" / "aws-sip-trunk",
        ConsumerType.AUTOMOTIVE_CAMERA: base_path / "consumers" / "automotive-camera",
        ConsumerType.PRINTCAST_AGENT: base_path / "consumers" / "printcast-agent",
        ConsumerType.ELEVENLABS_AGENTS: base_path / "consumers" / "elevenlabs-agents"
    }
    
    # Create all directories
    for dir_path in list(types.values()) + list(consumers.values()):
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return DirectoryStructure(base_path, types, consumers)

def restructure_by_type(structure: DirectoryStructure) -> None:
    """Restructure files by type."""
    
    # Templates
    templates_src = [
        "templates/",
        "cursor-templates/",
        "data/prompts/templates/",
        "mcp-project-orchestrator/openssl/"
    ]
    
    for src in templates_src:
        src_path = Path(src)
        if src_path.exists():
            dest_path = structure.types[DirectoryType.TEMPLATES] / src_path.name
            if src_path.is_dir():
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)
    
    # Scripts
    scripts_src = [
        "scripts/",
        "examples/"
    ]
    
    for src in scripts_src:
        src_path = Path(src)
        if src_path.exists():
            dest_path = structure.types[DirectoryType.SCRIPTS] / src_path.name
            if src_path.is_dir():
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)
    
    # Configs
    configs_src = [
        "config/",
        "component_templates.json",
        "project_orchestration.json",
        "project_templates.json"
    ]
    
    for src in configs_src:
        src_path = Path(src)
        if src_path.exists():
            dest_path = structure.types[DirectoryType.CONFIGS] / src_path.name
            if src_path.is_dir():
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)
    
    # MCP
    mcp_src = [
        "src/mcp_project_orchestrator/",
        "mcp-project-orchestrator/"
    ]
    
    for src in mcp_src:
        src_path = Path(src)
        if src_path.exists():
            dest_path = structure.types[DirectoryType.MCP] / src_path.name
            if src_path.is_dir():
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)
    
    # Docs
    docs_src = [
        "docs/",
        "*.md"
    ]
    
    for src in docs_src:
        if src.endswith("*.md"):
            # Copy all markdown files
            for md_file in Path(".").glob("*.md"):
                if md_file.name not in ["README.md"]:  # Skip main README
                    shutil.copy2(md_file, structure.types[DirectoryType.DOCS] / md_file.name)
        else:
            src_path = Path(src)
            if src_path.exists():
                dest_path = structure.types[DirectoryType.DOCS] / src_path.name
                if src_path.is_dir():
                    shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dest_path)

def restructure_by_consumers(structure: DirectoryStructure) -> None:
    """Restructure files by consumers."""
    
    # OpenSSL Tools (Python)
    openssl_tools_dest = structure.consumers[ConsumerType.OPENSSL_TOOLS]
    openssl_tools_dest.mkdir(parents=True, exist_ok=True)
    
    # Copy OpenSSL-specific files
    openssl_files = [
        "src/mcp_project_orchestrator/openssl_tools_orchestration.py",
        "src/mcp_project_orchestrator/openssl_orchestration_main.py", 
        "src/mcp_project_orchestrator/fips_compliance.py",
        "examples/openssl_tools_orchestration_example.py"
    ]
    
    for file_path in openssl_files:
        src = Path(file_path)
        if src.exists():
            dest = openssl_tools_dest / src.name
            shutil.copy2(src, dest)
    
    # Create OpenSSL Tools structure
    (openssl_tools_dest / "src").mkdir(exist_ok=True)
    (openssl_tools_dest / "tests").mkdir(exist_ok=True)
    (openssl_tools_dest / "scripts").mkdir(exist_ok=True)
    (openssl_tools_dest / "configs").mkdir(exist_ok=True)
    
    # OpenSSL Workflows (GitHub Actions YAML)
    openssl_workflows_dest = structure.consumers[ConsumerType.OPENSSL_WORKFLOWS]
    openssl_workflows_dest.mkdir(parents=True, exist_ok=True)
    
    # Create workflow templates
    workflow_templates = [
        "ci-cd.yml",
        "fips-validation.yml", 
        "release.yml",
        "security-scan.yml"
    ]
    
    for workflow in workflow_templates:
        workflow_path = openssl_workflows_dest / workflow
        workflow_path.write_text(f"# {workflow} - Generated workflow template\n")
    
    # AWS SIP Trunk
    aws_sip_dest = structure.consumers[ConsumerType.AWS_SIP_TRUNK]
    if Path("aws-sip-trunk/").exists():
        shutil.copytree("aws-sip-trunk/", aws_sip_dest, dirs_exist_ok=True)
    
    # Automotive Camera
    automotive_dest = structure.consumers[ConsumerType.AUTOMOTIVE_CAMERA]
    if Path("automotive-camera-system/").exists():
        shutil.copytree("automotive-camera-system/", automotive_dest, dirs_exist_ok=True)
    
    # Printcast Agent
    printcast_dest = structure.consumers[ConsumerType.PRINTCAST_AGENT]
    if Path("printcast-agent/").exists():
        shutil.copytree("printcast-agent/", printcast_dest, dirs_exist_ok=True)
    
    # ElevenLabs Agents
    elevenlabs_dest = structure.consumers[ConsumerType.ELEVENLABS_AGENTS]
    if Path("elevenlabs-agents/").exists():
        shutil.copytree("elevenlabs-agents/", elevenlabs_dest, dirs_exist_ok=True)

def create_conan_recipes(structure: DirectoryStructure) -> None:
    """Create Conan recipes for repositories without conanfile."""
    
    # OpenSSL Tools Conan recipe
    openssl_tools_conanfile = structure.consumers[ConsumerType.OPENSSL_TOOLS] / "conanfile.py"
    openssl_tools_conanfile.write_text('''#!/usr/bin/env python3
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
''')
    
    # OpenSSL Workflows Conan recipe
    openssl_workflows_conanfile = structure.consumers[ConsumerType.OPENSSL_WORKFLOWS] / "conanfile.py"
    openssl_workflows_conanfile.write_text('''#!/usr/bin/env python3
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
''')
    
    # AWS SIP Trunk Conan recipe
    aws_sip_conanfile = structure.consumers[ConsumerType.AWS_SIP_TRUNK] / "conanfile.py"
    aws_sip_conanfile.write_text('''#!/usr/bin/env python3
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
''')
    
    # Automotive Camera Conan recipe
    automotive_conanfile = structure.consumers[ConsumerType.AUTOMOTIVE_CAMERA] / "conanfile.py"
    automotive_conanfile.write_text('''#!/usr/bin/env python3
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
''')
    
    # Printcast Agent Conan recipe
    printcast_conanfile = structure.consumers[ConsumerType.PRINTCAST_AGENT] / "conanfile.py"
    printcast_conanfile.write_text('''#!/usr/bin/env python3
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
''')
    
    # ElevenLabs Agents Conan recipe
    elevenlabs_conanfile = structure.consumers[ConsumerType.ELEVENLABS_AGENTS] / "conanfile.py"
    elevenlabs_conanfile.write_text('''#!/usr/bin/env python3
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
''')

def create_cmake_files(structure: DirectoryStructure) -> None:
    """Create CMakeLists.txt files for C++ projects."""
    
    # OpenSSL Tools CMakeLists.txt
    openssl_tools_cmake = structure.consumers[ConsumerType.OPENSSL_TOOLS] / "CMakeLists.txt"
    openssl_tools_cmake.write_text('''cmake_minimum_required(VERSION 3.15)
project(OpenSSLToolsOrchestrator VERSION 0.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(OpenSSL REQUIRED)
find_package(ZLIB REQUIRED)

# Include directories
include_directories(include)

# Source files
file(GLOB_RECURSE SOURCES "src/*.cpp" "src/*.c")
file(GLOB_RECURSE HEADERS "include/*.h" "include/*.hpp")

# Create library
add_library(openssl_tools_orchestrator ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(openssl_tools_orchestrator 
    OpenSSL::SSL 
    OpenSSL::Crypto 
    ZLIB::ZLIB
)

# FIPS support
if(FIPS_ENABLED)
    target_compile_definitions(openssl_tools_orchestrator PRIVATE FIPS_MODE=1)
    find_package(FIPSCrypto REQUIRED)
    target_link_libraries(openssl_tools_orchestrator FIPSCrypto::FIPSCrypto)
endif()

# Install
install(TARGETS openssl_tools_orchestrator
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/ DESTINATION include)
''')
    
    # Automotive Camera CMakeLists.txt
    automotive_cmake = structure.consumers[ConsumerType.AUTOMOTIVE_CAMERA] / "CMakeLists.txt"
    automotive_cmake.write_text('''cmake_minimum_required(VERSION 3.15)
project(AutomotiveCameraSystem VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(OpenCV REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(GSTREAMER REQUIRED gstreamer-1.0)

# Include directories
include_directories(include)
include_directories(${OpenCV_INCLUDE_DIRS})
include_directories(${EIGEN3_INCLUDE_DIR})
include_directories(${GSTREAMER_INCLUDE_DIRS})

# Source files
file(GLOB_RECURSE SOURCES "src/*.cpp" "src/*.c")
file(GLOB_RECURSE HEADERS "include/*.h" "include/*.hpp")

# Create library
add_library(automotive_camera ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(automotive_camera 
    ${OpenCV_LIBS}
    ${EIGEN3_LIBRARIES}
    ${GSTREAMER_LIBRARIES}
)

# Install
install(TARGETS automotive_camera
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/ DESTINATION include)
''')

def create_package_manifests(structure: DirectoryStructure) -> None:
    """Create package manifests for each consumer."""
    
    # OpenSSL Tools package manifest
    openssl_manifest = structure.consumers[ConsumerType.OPENSSL_TOOLS] / "package_manifest.json"
    openssl_manifest.write_text(json.dumps({
        "name": "openssl-tools-orchestrator",
        "version": "0.2.0",
        "type": "python",
        "description": "OpenSSL Tools Orchestration with Agent Skills Integration",
        "dependencies": [
            "openssl>=3.1.0",
            "zlib>=1.3.0",
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
            "pydantic>=1.8.2",
            "pyyaml>=6.0",
            "rich>=10.12.0",
            "typer>=0.4.0"
        ],
        "build_system": "cmake",
        "platforms": ["linux", "windows", "macos"],
        "fips_support": True,
        "features": [
            "multi_platform_build",
            "fips_compliance",
            "ci_cd_automation",
            "agent_skills_integration",
            "security_validation"
        ]
    }, indent=2))
    
    # OpenSSL Workflows package manifest
    workflows_manifest = structure.consumers[ConsumerType.OPENSSL_WORKFLOWS] / "package_manifest.json"
    workflows_manifest.write_text(json.dumps({
        "name": "openssl-workflows",
        "version": "0.2.0",
        "type": "github_actions",
        "description": "GitHub Actions workflows for OpenSSL development",
        "workflows": [
            "ci-cd.yml",
            "fips-validation.yml",
            "release.yml",
            "security-scan.yml"
        ],
        "platforms": ["linux", "windows", "macos"],
        "triggers": ["push", "pull_request", "workflow_dispatch", "schedule", "release", "tag"],
        "features": [
            "multi_platform_ci",
            "fips_validation",
            "security_scanning",
            "automated_release",
            "matrix_builds"
        ]
    }, indent=2))

def main():
    """Main function to restructure directories and create Conan recipes."""
    
    print("🔄 Restructuring MCP Project Orchestrator directories...")
    
    # Create new directory structure
    base_path = Path("restructured")
    structure = create_directory_structure(base_path)
    
    print("📁 Created directory structure:")
    for dir_type, path in structure.types.items():
        print(f"  {dir_type.value}: {path}")
    
    for consumer_type, path in structure.consumers.items():
        print(f"  {consumer_type.value}: {path}")
    
    # Restructure by type
    print("\n📂 Restructuring by type...")
    restructure_by_type(structure)
    
    # Restructure by consumers
    print("👥 Restructuring by consumers...")
    restructure_by_consumers(structure)
    
    # Create Conan recipes
    print("📦 Creating Conan recipes...")
    create_conan_recipes(structure)
    
    # Create CMake files
    print("🔨 Creating CMake files...")
    create_cmake_files(structure)
    
    # Create package manifests
    print("📋 Creating package manifests...")
    create_package_manifests(structure)
    
    print("\n✅ Directory restructuring completed!")
    print(f"📁 New structure created in: {base_path}")
    
    # Create summary
    summary_path = base_path / "RESTRUCTURE_SUMMARY.md"
    summary_content = f"""# Directory Restructure Summary

## New Structure

### By Type
- **templates/**: All template files and configurations
- **scripts/**: Automation scripts and examples
- **configs/**: Configuration files and project settings
- **recipes/**: Conan recipes for package management
- **docs/**: Documentation and guides
- **mcp/**: MCP server and orchestration code

### By Consumers
- **openssl-tools/**: Python-based OpenSSL orchestration
- **openssl-workflows/**: GitHub Actions YAML workflows
- **aws-sip-trunk/**: AWS SIP Trunk deployment
- **automotive-camera/**: Automotive camera system
- **printcast-agent/**: Printcast agent application
- **elevenlabs-agents/**: ElevenLabs AI agents

## Conan Recipes Created

1. **openssl-tools-orchestrator**: OpenSSL Tools with Agent Skills
2. **openssl-workflows**: GitHub Actions workflows
3. **aws-sip-trunk**: AWS SIP Trunk deployment
4. **automotive-camera-system**: Automotive camera system
5. **printcast-agent**: Printcast agent application
6. **elevenlabs-agents**: ElevenLabs AI agents

## Features

- ✅ Organized by type and consumer
- ✅ Conan recipes for all repositories
- ✅ CMakeLists.txt for C++ projects
- ✅ Package manifests with dependencies
- ✅ FIPS compliance support
- ✅ Multi-platform support
- ✅ CI/CD integration ready

## Next Steps

1. Review the new structure
2. Test Conan recipes
3. Update build configurations
4. Deploy to package repositories
"""
    
    summary_path.write_text(summary_content)
    print(f"📄 Summary created: {summary_path}")

if __name__ == "__main__":
    main()