# Cursor Configuration Management

## Overview

Cursor configuration is managed like Conan profiles:
- **Templates** stored in package: `cursor-rules/`
- **Deployed** to each repository: `.cursor/`
- **Platform-specific** rules auto-selected
- **Developer customization** via `--custom-rules`

## Deployment Model

| Component | Location | Version Control |
|-----------|----------|-----------------|
| Templates | `mcp-project-orchestrator/openssl/cursor-rules/` | ✅ In package |
| Deployed config | `<repo>/.cursor/` | ✅ In repo (standard rules) |
| Custom rules | `<repo>/.cursor/rules/custom/` | ❌ Not committed (.gitignore) |

## Platform Detection

The deployer automatically detects:
- **OS**: Linux, macOS, Windows
- **CI environment**: GitHub Actions, GitLab CI, etc.
- **Python version**
- **User home directory**

## Usage

### Quick Start

```bash
# Install mcp-project-orchestrator/openssl
pip install mcp-project-orchestrator-openssl

# Deploy to current repository
mcp-orchestrator setup-cursor
```

### Advanced Options

```bash
# Force overwrite existing config
mcp-orchestrator setup-cursor --force

# Import custom rules
mcp-orchestrator setup-cursor \
  --custom-rules ~/my-rules/crypto.mdc \
  --custom-rules ~/my-rules/testing.mdc

# Opt out of AI features
mcp-orchestrator setup-cursor --opt-out

# Dry run (see what would be deployed)
mcp-orchestrator setup-cursor --dry-run
```

## Customization

### Scenario: Add Team-Specific Rules

1. Fork `mcp-project-orchestrator/openssl`
2. Edit `cursor-rules/rules/shared.mdc.jinja2`
3. Publish to private PyPI or install from Git

```bash
pip install git+https://github.com/mycompany/mcp-project-orchestrator/openssl.git@custom-rules
```

### Scenario: Disable MCP Servers

Edit `.cursor/mcp.json` manually:

```json
{
  "mcpServers": {
    "openssl-context": {
      "disabled": true
    }
  }
}
```

## Version Control Best Practices

Commit to Git:
- ✅ `.cursor/rules/*.mdc` (standard rules)
- ✅ `.cursor/prompts/*.md` (standard prompts)
- ✅ `.cursor/mcp.json` (MCP configuration)

Exclude from Git:
- ❌ `.cursor/rules/custom/` (personal rules)
- ❌ `.cursor/*.log`, `.cursor/*.cache`

## FAQ

**Q: Can I skip Cursor deployment entirely?**  
A: Yes, use `--opt-out` or set `MCP_ORCHESTRATOR_OPT_OUT=true`.

**Q: How do I update rules after package upgrade?**  
A: Run `mcp-orchestrator setup-cursor --force`.

**Q: Can I use my own rule templates?**  
A: Yes, use `--custom-rules` to import your files.

**Q: What if I want CI-specific rules locally?**  
A: Set `export CI=true` before running `setup-cursor`.

## Integration with OpenSSL Tools

### Setup Script Integration

```python
# openssl-tools/setup_openssl_env.py (UPDATED)
from openssl_conan_base.profile_deployer import deploy_conan_profiles
from mcp_orchestrator.cursor_deployer import CursorConfigDeployer
import click

@click.command()
@click.option('--with-cursor', is_flag=True, default=False,
              help='Also deploy Cursor AI configuration')
@click.option('--cursor-opt-out', is_flag=True, default=False,
              help='Skip Cursor configuration deployment')
def setup_environment(with_cursor, cursor_opt_out):
    """Setup OpenSSL development environment"""
    
    # Step 1: Deploy Conan profiles (always)
    click.echo("📦 Deploying Conan profiles...")
    deploy_conan_profiles()
    
    # Step 2: Deploy Cursor configuration (optional)
    if with_cursor and not cursor_opt_out:
        click.echo("🤖 Deploying Cursor AI configuration...")
        deployer = CursorConfigDeployer(Path.cwd(), get_mcp_package_root())
        deployer.deploy()
    elif cursor_opt_out:
        click.echo("⏭️  Skipping Cursor configuration (opt-out)")
    else:
        click.echo("ℹ️  Cursor configuration not deployed (use --with-cursor)")
    
    click.echo("✅ OpenSSL environment setup complete!")

if __name__ == '__main__':
    setup_environment()
```

## Summary: Cursor as Profile Management

| Aspect | Implementation |
| :-- | :-- |
| **Template Storage** | `mcp-project-orchestrator/openssl/cursor-rules/` (like `profiles/` in Conan packages) |
| **Deployment Target** | `<repo>/.cursor/` (like `~/.conan2/profiles/`) |
| **Platform Detection** | Auto-detect OS, CI, Python version (like profile selection logic) |
| **Customization** | `--custom-rules` flag (like profile inheritance/override) |
| **Opt-Out** | `--opt-out` flag or env var (like disabling Conan for a project) |
| **Version Control** | Standard rules committed, custom rules excluded (like shared profiles + local overrides) |
| **Update Strategy** | `--force` flag to re-deploy (like `conan config install --force`) |

This pattern provides:
- ✅ **Platform-specific** rules without manual selection
- ✅ **Developer opt-out** for those who don't want AI
- ✅ **Custom rule import** for personal preferences
- ✅ **CI environment** detection and adaptation
- ✅ **Reproducibility** through VCS-tracked standard rules
- ✅ **Flexibility** through local customization