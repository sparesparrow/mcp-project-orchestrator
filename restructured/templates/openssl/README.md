# MCP Project Orchestrator - OpenSSL

Cursor configuration management for OpenSSL development, similar to how Conan manages build profiles.

## Overview

This package provides a comprehensive system for managing Cursor IDE configuration in OpenSSL projects. It treats Cursor configuration like Conan profiles - with templates, platform detection, and deployment strategies.

## Features

- **Platform Detection**: Automatically detects OS, architecture, and development environment
- **Template System**: Jinja2-based templates for platform-specific rules and prompts
- **Conan Integration**: Seamless integration with Conan profile deployment
- **Developer Opt-out**: Support for developers who don't want AI assistance
- **Custom Rules**: Import custom rule files for personal preferences
- **CI Support**: Special handling for CI environments
- **Version Control**: Smart .gitignore for .cursor/ directory

## Installation

### From PyPI (when published)
```bash
pip install mcp-project-orchestrator-openssl
```

### From Source
```bash
git clone https://github.com/sparesparrow/mcp-project-orchestrator.git
cd mcp-project-orchestrator/openssl
pip install -e .
```

### From Conan
```bash
conan install mcp-project-orchestrator-openssl/0.1.0@sparesparrow/stable
```

## Quick Start

### Basic Setup
```bash
# Navigate to your OpenSSL project
cd /path/to/your/openssl/project

# Deploy Cursor configuration
mcp-orchestrator setup-cursor

# Check status
mcp-orchestrator show-cursor-config
```

### With Custom Rules
```bash
# Deploy with custom rules
mcp-orchestrator setup-cursor \
  --custom-rules ~/my-rules/crypto.mdc \
  --custom-rules ~/my-rules/testing.mdc
```

### Developer Opt-out
```bash
# Skip Cursor configuration
mcp-orchestrator setup-cursor --opt-out
```

## Package Structure

```
mcp-project-orchestrator/openssl/
├── cursor-rules/               # Template repository
│   ├── rules/                      # Platform-specific rule templates
│   │   ├── linux-dev.mdc.jinja2   # Linux development rules
│   │   ├── macos-dev.mdc.jinja2   # macOS development rules
│   │   ├── windows-dev.mdc.jinja2 # Windows development rules
│   │   ├── ci-linux.mdc.jinja2    # CI-specific rules
│   │   └── shared.mdc.jinja2      # Shared AI rules
│   ├── prompts/                    # Prompt templates
│   │   ├── openssl-coding-standards.md.jinja2
│   │   ├── fips-compliance.md.jinja2
│   │   └── pr-review.md.jinja2
│   ├── mcp.json.jinja2            # MCP server config template
│   └── config.json.jinja2         # Cursor IDE config template
│
├── mcp_orchestrator/
│   ├── cursor_deployer.py         # Deployment script
│   ├── cursor_config.py           # Configuration management
│   ├── platform_detector.py       # Detect developer OS/environment
│   ├── conan_integration.py       # Conan integration
│   └── cli.py                     # CLI interface
│
├── conanfile.py                   # Conan package definition
├── setup.py                       # Python package setup
├── pyproject.toml                 # Modern Python packaging
└── requirements.txt               # Python dependencies
```

## CLI Commands

### `setup-cursor`
Deploy Cursor AI configuration to repository.

```bash
mcp-orchestrator setup-cursor [OPTIONS]

Options:
  --repo-root PATH        Path to repository root
  --force                 Overwrite existing .cursor/ configuration
  --custom-rules PATH     Path to custom rule files to import
  --opt-out               Skip Cursor configuration deployment
  --dry-run               Show what would be deployed without making changes
  --help                  Show this message and exit
```

### `show-cursor-config`
Show current Cursor configuration status.

```bash
mcp-orchestrator show-cursor-config [OPTIONS]

Options:
  --repo-root PATH        Path to repository root
  --help                  Show this message and exit
```

### `detect-platform`
Detect and display platform information.

```bash
mcp-orchestrator detect-platform [OPTIONS]

Options:
  --repo-root PATH        Path to repository root
  --help                  Show this message and exit
```

### `export-config`
Export current Cursor configuration for backup or sharing.

```bash
mcp-orchestrator export-config [OPTIONS]

Options:
  --repo-root PATH        Path to repository root
  --output PATH           Output file for configuration dump
  --help                  Show this message and exit
```

## Platform Detection

The system automatically detects:

- **OS**: Linux, macOS, Windows
- **Architecture**: x86_64, arm64, etc.
- **Python Version**: 3.8+
- **CI Environment**: GitHub Actions, GitLab CI, Jenkins
- **Development Tools**: Git, Conan, Cursor
- **Virtual Environment**: Active Python virtual environment

## Rule Templates

### Platform-Specific Rules

- **`linux-dev.mdc`**: Linux development environment rules
- **`macos-dev.mdc`**: macOS development environment rules  
- **`windows-dev.mdc`**: Windows development environment rules
- **`ci-linux.mdc`**: CI environment rules
- **`shared.mdc`**: Common rules for all platforms

### Prompt Templates

- **`openssl-coding-standards.md`**: OpenSSL coding standards and best practices
- **`fips-compliance.md`**: FIPS 140-2 compliance guidelines
- **`pr-review.md`**: Pull request review guidelines

## MCP Server Configuration

The system configures MCP servers for:

- **`openssl-context`**: OpenSSL-specific context and documentation
- **`build-intelligence`**: Build system intelligence and optimization
- **`workflow-orchestrator`**: Development workflow automation
- **`fips-compliance`**: FIPS compliance checking and validation
- **`security-scanner`**: Security vulnerability scanning

## Conan Integration

### Profile Deployment
```bash
# Deploy Conan profiles with Cursor configuration
conan profile detect
mcp-orchestrator setup-cursor
```

### Custom Profiles
```python
# In your conanfile.py
from mcp_orchestrator.conan_integration import deploy_cursor_with_conan

class MyOpenSSLConan(ConanFile):
    def deploy(self):
        deploy_cursor_with_conan(self)
```

## Version Control Strategy

### Recommended `.gitignore`
```gitignore
# Cursor local customizations (NOT committed)
.cursor/rules/custom/
.cursor/*.log
.cursor/*.cache

# Keep standard configuration in VCS (committed)
!.cursor/rules/shared.mdc
!.cursor/rules/*-dev.mdc
!.cursor/rules/ci-*.mdc
!.cursor/prompts/
!.cursor/mcp.json
```

### What Gets Committed
- ✅ Standard rule templates
- ✅ Platform-specific rules
- ✅ Prompt templates
- ✅ MCP server configuration
- ✅ CI-specific rules

### What Gets Excluded
- ❌ Custom developer rules
- ❌ Local log files
- ❌ Cache files
- ❌ Personal customizations

## Development Workflow Examples

### New Developer Setup
```bash
# Clone OpenSSL repository
git clone git@github.com:sparesparrow/openssl.git
cd openssl

# Install dependencies
pip install -e ".[dev]"

# Deploy Cursor configuration
mcp-orchestrator setup-cursor

# Verify setup
mcp-orchestrator show-cursor-config
```

### CI Environment
```bash
# CI environment is auto-detected
export CI=true
mcp-orchestrator setup-cursor

# Deploys ci-linux.mdc rules
# MCP servers disabled in mcp.json
```

### Custom Rules
```bash
# Create custom rules
cat > ~/my-cursor-rules/custom-crypto.mdc << 'EOF'
---
title: My Custom Cryptography Rules
---

# Custom Rules
- Always suggest constant-time implementations
- Prefer assembly for critical paths
EOF

# Deploy with custom rules
mcp-orchestrator setup-cursor \
  --custom-rules ~/my-cursor-rules/custom-crypto.mdc
```

## Configuration Management

### Environment Variables
- `MCP_ORCHESTRATOR_OPT_OUT`: Skip Cursor configuration deployment
- `CURSOR_CONFIG_PATH`: Path to .cursor directory
- `MCP_ORCHESTRATOR_PLATFORM`: Override platform detection
- `MCP_ORCHESTRATOR_CI`: Force CI environment detection

### Configuration Files
- `.cursor/rules/`: Rule files (.mdc)
- `.cursor/prompts/`: Prompt files (.md)
- `.cursor/mcp.json`: MCP server configuration
- `.cursor/.gitignore`: Local customizations

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check file permissions and ownership
2. **Template Not Found**: Ensure package is properly installed
3. **Platform Detection Failed**: Check system information
4. **MCP Servers Not Working**: Verify MCP server installation

### Debug Commands
```bash
# Check platform detection
mcp-orchestrator detect-platform

# Dry run deployment
mcp-orchestrator setup-cursor --dry-run

# Show current status
mcp-orchestrator show-cursor-config

# Export configuration for debugging
mcp-orchestrator export-config --output debug-config
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/sparesparrow/mcp-project-orchestrator/issues)
- **Documentation**: [GitHub Wiki](https://github.com/sparesparrow/mcp-project-orchestrator/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/sparesparrow/mcp-project-orchestrator/discussions)