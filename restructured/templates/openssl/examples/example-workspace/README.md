# Example OpenSSL Workspace with Cursor AI Configuration

This example workspace demonstrates how Cursor AI configuration maps to Conan profiles in OpenSSL development.

## Overview

This workspace shows the complete integration between:
- **Conan Profiles**: Build system configuration
- **Cursor AI Configuration**: IDE assistance and development rules
- **MCP Servers**: AI-powered development tools

## Directory Structure

```
example-workspace/
├── .cursor/                          # Cursor AI configuration
│   ├── rules/                        # Development rules (like Conan profiles)
│   │   ├── shared.mdc               # Common rules for all platforms
│   │   ├── linux-dev.mdc            # Linux-specific rules
│   │   ├── macos-dev.mdc            # macOS-specific rules
│   │   ├── windows-dev.mdc          # Windows-specific rules
│   │   └── ci-linux.mdc             # CI environment rules
│   ├── prompts/                      # AI prompt templates
│   │   ├── openssl-coding-standards.md
│   │   ├── fips-compliance.md
│   │   └── pr-review.md
│   ├── mcp.json                     # MCP server configuration
│   └── .gitignore                   # Local customizations (not committed)
│
├── profiles/                         # Conan build profiles
│   ├── linux-gcc-release.profile    # Linux release build
│   ├── linux-gcc-debug.profile      # Linux debug build
│   ├── macos-clang-release.profile  # macOS release build
│   ├── windows-msvc-release.profile # Windows release build
│   └── ci-linux.profile             # CI build profile
│
├── conanfile.py                     # Conan package definition
├── CMakeLists.txt                   # CMake build configuration
├── README.md                        # This file
└── .gitignore                       # Git ignore rules
```

## Cursor Settings to Conan Profiles Mapping

### 1. Platform Detection

| Cursor Rule | Conan Profile | Description |
|-------------|---------------|-------------|
| `linux-dev.mdc` | `linux-gcc-release.profile` | Linux development environment |
| `macos-dev.mdc` | `macos-clang-release.profile` | macOS development environment |
| `windows-dev.mdc` | `windows-msvc-release.profile` | Windows development environment |
| `ci-linux.mdc` | `ci-linux.profile` | CI build environment |

### 2. Environment Variables

| Cursor Configuration | Conan Profile | Purpose |
|---------------------|---------------|---------|
| `CONAN_USER_HOME` | `[env]` section | Package cache location |
| `OPENSSL_ROOT_DIR` | `[env]` section | OpenSSL installation path |
| `PKG_CONFIG_PATH` | `[env]` section | Library discovery |
| `CC`, `CXX` | `[settings]` | Compiler selection |

### 3. Build Configuration

| Cursor Rule | Conan Profile | Mapping |
|-------------|---------------|---------|
| Compiler defaults | `compiler` setting | Platform-specific compiler |
| Optimization flags | `build_type` setting | Debug vs Release |
| Architecture | `arch` setting | x86_64, arm64, etc. |
| Library type | `shared` option | Static vs Dynamic linking |

### 4. MCP Servers to Conan Integration

| MCP Server | Conan Integration | Purpose |
|------------|-------------------|---------|
| `openssl-context` | Profile environment | OpenSSL-specific context |
| `build-intelligence` | Build optimization | Build system intelligence |
| `fips-compliance` | FIPS validation | Compliance checking |
| `security-scanner` | Security audit | Vulnerability scanning |

## Usage Examples

### 1. Deploy Cursor Configuration

```bash
# Deploy Cursor configuration (like Conan profile detection)
deploy-cursor --project-type openssl

# Deploy with custom rules
deploy-cursor --project-type openssl --custom-rules ~/my-rules/crypto.mdc

# Check environment variables
deploy-cursor --project-type openssl --check-env --verbose
```

### 2. Deploy Conan Profiles

```bash
# Deploy Conan profiles (existing functionality)
conan profile detect
conan profile show default

# Use specific profile
conan install . --profile=linux-gcc-release
```

### 3. Combined Workflow

```bash
# 1. Deploy Conan profiles
conan profile detect

# 2. Deploy Cursor configuration
deploy-cursor --project-type openssl

# 3. Build with both configurations
conan install . --profile=linux-gcc-release
cmake --build build/
```

## Configuration Files

### Cursor AI Rules (.mdc files)

Each `.mdc` file contains:
- **YAML Frontmatter**: Metadata (title, platform, user, etc.)
- **Markdown Content**: Development rules and guidelines
- **Platform-specific**: Tailored for each development environment

Example `linux-dev.mdc`:
```yaml
---
title: OpenSSL Development (Linux)
description: Linux-specific development rules
platform: linux
user: developer
created: 2024-01-01T00:00:00
---

# Linux Development Rules

## Compiler Defaults
- Default to GCC unless clang is explicitly requested
- Use `-fPIC` for shared libraries
- Enable `-O2` optimization for release builds
```

### Conan Profiles (.profile files)

Each `.profile` file contains:
- **Settings**: Compiler, architecture, build type
- **Options**: Package-specific configuration
- **Environment**: Environment variables

Example `linux-gcc-release.profile`:
```ini
[settings]
os=Linux
arch=x86_64
compiler=gcc
compiler.version=11
compiler.libcxx=libstdc++11
build_type=Release

[options]
*:shared=True

[env]
CONAN_USER_HOME=/home/user/.conan2
OPENSSL_ROOT_DIR=/usr/local
PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
```

### MCP Server Configuration (mcp.json)

```json
{
  "mcpServers": {
    "openssl-context": {
      "command": "npx",
      "args": ["-y", "@sparesparrow/mcp-openssl-context"],
      "env": {
        "OPENSSL_PROJECT_ROOT": "/path/to/project",
        "CONAN_USER_HOME": "/home/user/.conan2",
        "PLATFORM": "linux"
      }
    }
  }
}
```

## Development Workflow

### 1. New Developer Setup

```bash
# Clone repository
git clone <repository-url>
cd openssl-project

# Install dependencies
pip install mcp-project-orchestrator-openssl

# Deploy Conan profiles
conan profile detect

# Deploy Cursor configuration
deploy-cursor --project-type openssl

# Verify setup
mcp-orchestrator show-cursor-config
conan profile show default
```

### 2. CI/CD Pipeline

```bash
# CI environment automatically detected
export CI=true

# Deploy configurations
conan profile detect
deploy-cursor --project-type openssl

# Build with CI profile
conan install . --profile=ci-linux
cmake --build build/
```

### 3. Custom Development

```bash
# Add custom rules
deploy-cursor --project-type openssl \
  --custom-rules ~/my-rules/crypto.mdc \
  --custom-rules ~/my-rules/testing.mdc

# Force update configuration
deploy-cursor --project-type openssl --force
```

## Benefits of Integration

### 1. Consistency
- **Conan Profiles**: Consistent build environments
- **Cursor Rules**: Consistent development practices
- **MCP Servers**: Consistent AI assistance

### 2. Platform Awareness
- **Automatic Detection**: Platform-specific configuration
- **Environment Variables**: Proper toolchain setup
- **Build Optimization**: Platform-specific optimizations

### 3. Developer Experience
- **One Command Setup**: Deploy both Conan and Cursor configs
- **Environment Validation**: Check required variables
- **Custom Rules**: Personal development preferences

### 4. CI/CD Integration
- **Automated Deployment**: CI-specific configurations
- **Validation**: Template and schema validation
- **Artifacts**: Build artifacts and configuration exports

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```bash
   # Check environment variables
   deploy-cursor --project-type openssl --check-env --verbose
   
   # Set required variables
   export CONAN_USER_HOME=~/.conan2
   export OPENSSL_ROOT_DIR=/usr/local
   ```

2. **Template Rendering Errors**
   ```bash
   # Validate templates
   python -m mcp_orchestrator.yaml_validator .cursor/rules/
   
   # Test template rendering
   python -m pytest tests/test_template_validation.py
   ```

3. **Configuration Validation**
   ```bash
   # Validate MCP configuration
   python -c "import json; json.load(open('.cursor/mcp.json'))"
   
   # Check Conan profiles
   conan profile show default
   ```

## Conclusion

This example demonstrates how Cursor AI configuration seamlessly integrates with Conan profiles to provide a comprehensive development environment for OpenSSL projects. The mapping between Cursor settings and Conan profiles ensures consistency across build systems and development tools.