#!/usr/bin/env python3
"""
Test script for Cursor configuration deployment.

This script tests the basic functionality of the Cursor configuration deployer.
"""

import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the package to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_orchestrator.cursor_deployer import CursorConfigDeployer
from mcp_orchestrator.platform_detector import PlatformDetector


def create_test_templates(package_root):
    """Create test template files."""
    templates_dir = package_root / "cursor-rules"
    templates_dir.mkdir(parents=True)
    
    # Create rules directory
    rules_dir = templates_dir / "rules"
    rules_dir.mkdir(parents=True)
    
    # Create prompts directory
    prompts_dir = templates_dir / "prompts"
    prompts_dir.mkdir(parents=True)
    
    # Create shared rule template
    shared_template = rules_dir / "shared.mdc.jinja2"
    shared_template.write_text("""---
title: Shared Rules
description: Common rules for all platforms
created: {{ timestamp }}
platform: shared
user: {{ user }}
---

# Shared Rules

This is a test shared rule template.
Platform: {{ os }}
User: {{ user }}
""")
    
    # Create Linux rule template
    linux_template = rules_dir / "linux-dev.mdc.jinja2"
    linux_template.write_text("""---
title: Linux Development Rules
description: Linux-specific development rules
created: {{ timestamp }}
platform: linux
user: {{ user }}
---

# Linux Development Rules

This is a test Linux rule template.
OS: {{ os }}
Architecture: {{ architecture }}
""")
    
    # Create prompt template
    prompt_template = prompts_dir / "test-prompt.md.jinja2"
    prompt_template.write_text("""# Test Prompt

This is a test prompt template.
Platform: {{ os }}
User: {{ user }}
""")
    
    # Create MCP config template
    mcp_template = templates_dir / "mcp.json.jinja2"
    mcp_template.write_text("""{
  "mcpServers": {
    "test-server": {
      "command": "{{ platform_detector.get_mcp_command() }}",
      "args": ["-y", "@test/mcp-server"],
      "env": {
        "PLATFORM": "{{ os }}",
        "USER": "{{ user }}"
      }
    }
  }
}
""")


def test_platform_detection():
    """Test platform detection."""
    print("🔍 Testing platform detection...")
    
    detector = PlatformDetector()
    platform_info = detector.detect_platform()
    
    print(f"   OS: {platform_info['os']}")
    print(f"   Architecture: {platform_info['architecture']}")
    print(f"   Python: {platform_info['python_version']}")
    print(f"   User: {platform_info['user']}")
    print(f"   CI Environment: {platform_info['is_ci']}")
    
    return platform_info


def test_deployment():
    """Test Cursor configuration deployment."""
    print("\n🤖 Testing Cursor configuration deployment...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test repository
        repo_root = temp_path / "test_repo"
        repo_root.mkdir()
        
        # Create test package
        package_root = temp_path / "test_package"
        package_root.mkdir()
        
        # Create test templates
        create_test_templates(package_root)
        
        # Create deployer
        deployer = CursorConfigDeployer(repo_root, package_root)
        
        # Test platform detection
        platform_info = deployer.detect_platform()
        print(f"   Detected platform: {platform_info['os']}")
        
        # Test dry run
        print("   Testing dry run...")
        deployer.dry_run()
        
        # Test deployment
        print("   Testing deployment...")
        deployer.deploy()
        
        # Check results
        cursor_dir = repo_root / ".cursor"
        assert cursor_dir.exists(), ".cursor directory should be created"
        
        rules_dir = cursor_dir / "rules"
        assert rules_dir.exists(), "rules directory should be created"
        
        prompts_dir = cursor_dir / "prompts"
        assert prompts_dir.exists(), "prompts directory should be created"
        
        # Check that shared rule was deployed
        shared_rule = rules_dir / "shared.mdc"
        assert shared_rule.exists(), "shared rule should be deployed"
        
        # Check that platform-specific rule was deployed
        os_name = platform_info["os"]
        platform_rule = rules_dir / f"{os_name}-dev.mdc"
        assert platform_rule.exists(), f"{os_name}-dev rule should be deployed"
        
        # Check that prompt was deployed
        prompt_file = prompts_dir / "test-prompt.md"
        assert prompt_file.exists(), "test prompt should be deployed"
        
        # Check that MCP config was deployed
        mcp_config = cursor_dir / "mcp.json"
        assert mcp_config.exists(), "MCP config should be deployed"
        
        # Test status display
        print("   Testing status display...")
        deployer.show_status()
        
        print("   ✅ Deployment test passed!")


def test_custom_rules():
    """Test deployment with custom rules."""
    print("\n📦 Testing custom rules deployment...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test repository
        repo_root = temp_path / "test_repo"
        repo_root.mkdir()
        
        # Create test package
        package_root = temp_path / "test_package"
        package_root.mkdir()
        
        # Create test templates
        create_test_templates(package_root)
        
        # Create custom rule file
        custom_rule = temp_path / "custom-rule.mdc"
        custom_rule.write_text("""---
title: Custom Rule
description: A custom rule for testing
---

# Custom Rule

This is a custom rule.
""")
        
        # Create deployer
        deployer = CursorConfigDeployer(repo_root, package_root)
        
        # Deploy with custom rules
        deployer.deploy(custom_rules=[custom_rule])
        
        # Check that custom rule was imported
        custom_dir = repo_root / ".cursor" / "rules" / "custom"
        assert custom_dir.exists(), "custom rules directory should be created"
        
        imported_rule = custom_dir / "custom-rule.mdc"
        assert imported_rule.exists(), "custom rule should be imported"
        
        print("   ✅ Custom rules test passed!")


def test_opt_out():
    """Test opt-out functionality."""
    print("\n⏭️  Testing opt-out functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test repository
        repo_root = temp_path / "test_repo"
        repo_root.mkdir()
        
        # Create test package
        package_root = temp_path / "test_package"
        package_root.mkdir()
        
        # Create test templates
        create_test_templates(package_root)
        
        # Create deployer
        deployer = CursorConfigDeployer(repo_root, package_root)
        
        # Deploy with opt-out
        deployer.deploy(opt_out=True)
        
        # Check that .cursor directory was not created
        cursor_dir = repo_root / ".cursor"
        assert not cursor_dir.exists(), ".cursor directory should not be created with opt-out"
        
        print("   ✅ Opt-out test passed!")


def main():
    """Run all tests."""
    print("🧪 Running Cursor configuration deployment tests...\n")
    
    try:
        # Test platform detection
        test_platform_detection()
        
        # Test basic deployment
        test_deployment()
        
        # Test custom rules
        test_custom_rules()
        
        # Test opt-out
        test_opt_out()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()