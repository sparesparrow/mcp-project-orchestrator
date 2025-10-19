# MCP Project Orchestrator - Directory Structure Guide

## Overview

This document describes the restructured directory organization for the MCP Project Orchestrator ecosystem, organized by type and consumers with comprehensive Conan package management.

## Directory Structure

```
restructured/
├── templates/                    # All template files and configurations
│   ├── cursor-templates/        # Cursor IDE templates
│   ├── openssl/                 # OpenSSL-specific templates
│   └── templates/               # General project templates
├── scripts/                     # Automation scripts and examples
│   ├── examples/                # Usage examples
│   └── scripts/                 # Build and deployment scripts
├── configs/                     # Configuration files and project settings
│   ├── config/                  # Core configuration files
│   ├── component_templates.json
│   ├── project_orchestration.json
│   └── project_templates.json
├── recipes/                     # Conan recipes for package management
│   ├── mcp-project-orchestrator/
│   ├── openssl-fips-validator/
│   ├── agent-skills-framework/
│   └── [other package recipes]
├── docs/                        # Documentation and guides
│   ├── docs/                    # Core documentation
│   └── [various .md files]
├── mcp/                         # MCP server and orchestration code
│   ├── mcp_project_orchestrator/
│   └── mcp-project-orchestrator/
├── consumers/                   # Consumer applications organized by type
│   ├── openssl-tools/           # Python-based OpenSSL orchestration
│   ├── openssl-workflows/       # GitHub Actions YAML workflows
│   ├── aws-sip-trunk/           # AWS SIP Trunk deployment
│   ├── automotive-camera/       # Automotive camera system
│   ├── printcast-agent/         # Printcast agent application
│   └── elevenlabs-agents/       # ElevenLabs AI agents
└── package_management/          # Package management configuration
    ├── conanfile.txt
    └── conanfile.py
```

## Organization by Type

### 1. Templates (`templates/`)
Contains all template files and configurations organized by purpose:

- **`cursor-templates/`**: Cursor IDE-specific templates
- **`openssl/`**: OpenSSL development templates
- **`templates/`**: General project templates

**Key Files:**
- `*.jinja2`: Jinja2 template files
- `*.json`: JSON template configurations
- `*.md`: Markdown template files

### 2. Scripts (`scripts/`)
Automation scripts and examples:

- **`examples/`**: Usage examples and demonstrations
- **`scripts/`**: Build, deployment, and utility scripts

**Key Files:**
- `build_all_packages.sh`: Complete package build script
- `setup_*.sh`: Setup and installation scripts
- `*.py`: Python utility scripts

### 3. Configs (`configs/`)
Configuration files and project settings:

- **`config/`**: Core configuration files
- `component_templates.json`: Component template definitions
- `project_orchestration.json`: Project orchestration configuration
- `project_templates.json`: Project template definitions

### 4. Recipes (`recipes/`)
Conan recipes for package management:

- **`mcp-project-orchestrator/`**: Core MCP orchestrator package
- **`openssl-fips-validator/`**: FIPS compliance validator
- **`agent-skills-framework/`**: Agent Skills framework
- **`[package-name]/`**: Individual package recipes

**Key Files:**
- `conanfile.py`: Conan package recipe
- `CMakeLists.txt`: CMake build configuration (for C++ packages)
- `package_manifest.json`: Package metadata and dependencies

### 5. Docs (`docs/`)
Documentation and guides:

- **`docs/`**: Core documentation
- Various `.md` files with implementation guides and summaries

### 6. MCP (`mcp/`)
MCP server and orchestration code:

- **`mcp_project_orchestrator/`**: Main MCP orchestrator implementation
- **`mcp-project-orchestrator/`**: Additional MCP components

## Organization by Consumers

### 1. OpenSSL Tools (`consumers/openssl-tools/`)
Python-based OpenSSL orchestration system:

**Structure:**
```
openssl-tools/
├── conanfile.py                 # Conan package recipe
├── CMakeLists.txt              # CMake build configuration
├── package_manifest.json       # Package metadata
├── src/                        # Source code directory
├── tests/                      # Test suites
├── scripts/                    # OpenSSL-specific scripts
├── configs/                    # OpenSSL configurations
├── fips_compliance.py          # FIPS compliance validator
├── openssl_orchestration_main.py
├── openssl_tools_orchestration.py
└── openssl_tools_orchestration_example.py
```

**Features:**
- FIPS 140-3 compliance validation
- Multi-platform build support
- Agent Skills integration
- Comprehensive testing framework

### 2. OpenSSL Workflows (`consumers/openssl-workflows/`)
GitHub Actions YAML workflows:

**Structure:**
```
openssl-workflows/
├── conanfile.py                # Conan package recipe
├── package_manifest.json       # Package metadata
├── ci-cd.yml                   # Main CI/CD workflow
├── fips-validation.yml         # FIPS validation workflow
├── release.yml                 # Release workflow
└── security-scan.yml           # Security scanning workflow
```

**Features:**
- Multi-platform CI/CD
- FIPS validation automation
- Security scanning integration
- Automated release management

### 3. AWS SIP Trunk (`consumers/aws-sip-trunk/`)
AWS SIP Trunk deployment system:

**Structure:**
```
aws-sip-trunk/
├── conanfile.py                # Conan package recipe
├── terraform/                  # Terraform infrastructure
├── config/                     # Asterisk configuration
├── scripts/                    # Deployment scripts
├── tests/                      # Test suites
├── docs/                       # Documentation
└── pyproject.toml              # Python project configuration
```

**Features:**
- Terraform infrastructure as code
- Asterisk configuration management
- AWS deployment automation
- Comprehensive testing

### 4. Automotive Camera (`consumers/automotive-camera/`)
Automotive camera system:

**Structure:**
```
automotive-camera/
├── conanfile.py                # Conan package recipe
├── CMakeLists.txt              # CMake build configuration
├── docs/                       # Documentation
└── README.md                   # Project overview
```

**Features:**
- Computer vision integration
- Real-time processing
- OpenCV and GStreamer support
- Cross-platform build support

### 5. Printcast Agent (`consumers/printcast-agent/`)
Printcast agent application:

**Structure:**
```
printcast-agent/
├── conanfile.py                # Conan package recipe
├── src/                        # Source code
├── tests/                      # Test suites
├── scripts/                    # Utility scripts
├── config/                     # Configuration files
├── docker-compose.yml          # Docker composition
├── Containerfile               # Container definition
└── pyproject.toml              # Python project configuration
```

**Features:**
- Docker containerization
- Web interface
- Print management
- Configuration management

### 6. ElevenLabs Agents (`consumers/elevenlabs-agents/`)
ElevenLabs AI agents:

**Structure:**
```
elevenlabs-agents/
├── conanfile.py                # Conan package recipe
├── agent-prompts.json          # Agent prompt configurations
└── README.md                   # Project overview
```

**Features:**
- AI agent management
- Voice synthesis integration
- Natural language processing
- Prompt configuration

## Conan Package Management

### Package Dependencies

The complete ecosystem includes the following packages:

1. **Core Packages:**
   - `mcp-project-orchestrator`: Main MCP orchestrator
   - `agent-skills-framework`: Agent Skills framework
   - `openssl-fips-validator`: FIPS compliance validator

2. **Consumer Packages:**
   - `openssl-tools-orchestrator`: OpenSSL tools orchestration
   - `openssl-workflows`: GitHub Actions workflows
   - `aws-sip-trunk`: AWS SIP Trunk deployment
   - `automotive-camera-system`: Automotive camera system
   - `printcast-agent`: Printcast agent application
   - `elevenlabs-agents`: ElevenLabs AI agents

3. **Complete Package:**
   - `mcp-project-orchestrator-complete`: Complete ecosystem package

### Build Profiles

The system supports multiple build profiles:

- **Linux GCC 11**: Release and Debug
- **Windows MSVC 193**: Release and Debug
- **macOS Clang**: Release and Debug

### Package Features

Each package includes:

- **FIPS Support**: Optional FIPS 140-3 compliance
- **AWS Integration**: Optional AWS services integration
- **Cursor Integration**: Optional Cursor IDE integration
- **Multi-platform**: Cross-platform build support
- **Security**: Comprehensive security validation
- **Testing**: Automated testing framework

## Usage Examples

### Building All Packages

```bash
# Build all packages with all profiles
./scripts/build_all_packages.sh

# Build and upload to remote
./scripts/build_all_packages.sh --upload
```

### Installing a Specific Package

```bash
# Install OpenSSL Tools Orchestrator
conan install openssl-tools-orchestrator/0.2.0@sparesparrow/stable

# Install with specific profile
conan install openssl-tools-orchestrator/0.2.0@sparesparrow/stable \
    --profile=profiles/linux-gcc11-release
```

### Using the Complete Package

```bash
# Install complete ecosystem
conan install mcp-project-orchestrator-complete/0.2.0@sparesparrow/stable

# Activate environment
conan activate mcp-project-orchestrator-complete/0.2.0@sparesparrow/stable
```

## Development Workflow

### 1. Package Development

1. **Create Package Structure:**
   ```bash
   mkdir -p recipes/new-package
   cd recipes/new-package
   # Create conanfile.py and other files
   ```

2. **Test Package:**
   ```bash
   conan create . sparesparrow/stable --profile=profiles/linux-gcc11-release
   ```

3. **Upload Package:**
   ```bash
   conan upload new-package --all --remote=mcp-orchestrator --confirm
   ```

### 2. Consumer Development

1. **Create Consumer Structure:**
   ```bash
   mkdir -p consumers/new-consumer
   cd consumers/new-consumer
   # Create consumer-specific files
   ```

2. **Add Conan Recipe:**
   ```bash
   # Create conanfile.py for the consumer
   ```

3. **Test Integration:**
   ```bash
   conan install . --build=missing
   ```

## Benefits of This Structure

### 1. **Clear Organization**
- Files organized by type and purpose
- Easy to find and maintain components
- Logical separation of concerns

### 2. **Package Management**
- Comprehensive Conan integration
- Dependency management
- Version control and distribution

### 3. **Multi-Platform Support**
- Cross-platform build configurations
- Platform-specific optimizations
- Consistent build process

### 4. **Consumer-Specific Optimization**
- Tailored configurations for each consumer
- Optimized dependencies
- Specialized build processes

### 5. **Development Efficiency**
- Reusable components
- Automated build and test processes
- Comprehensive documentation

## Migration Guide

### From Old Structure

1. **Identify Package Type:**
   - Determine if it's a template, script, config, or consumer
   - Move to appropriate directory

2. **Create Conan Recipe:**
   - Add `conanfile.py` for package management
   - Define dependencies and options

3. **Update Build Process:**
   - Use new build scripts
   - Update CI/CD configurations

4. **Test Integration:**
   - Verify package builds correctly
   - Test consumer integration

### To New Structure

1. **Review Dependencies:**
   - Check package dependencies
   - Update version requirements

2. **Update Build Scripts:**
   - Use new build system
   - Update deployment processes

3. **Test Everything:**
   - Build all packages
   - Run integration tests
   - Verify functionality

## Conclusion

This restructured directory organization provides:

- **Clear separation** of concerns by type and consumer
- **Comprehensive package management** with Conan
- **Multi-platform support** for all components
- **Easy maintenance** and development
- **Scalable architecture** for future growth

The structure supports the complete MCP Project Orchestrator ecosystem while maintaining flexibility for individual consumer needs and requirements.