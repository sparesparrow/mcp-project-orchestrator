"""
Tests for Cursor configuration deployer.

This module contains tests for the CursorConfigDeployer class and related functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from mcp_orchestrator.cursor_deployer import CursorConfigDeployer
from mcp_orchestrator.platform_detector import PlatformDetector
from mcp_orchestrator.cursor_config import CursorConfig


class TestCursorConfigDeployer:
    """Test cases for CursorConfigDeployer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "test_repo"
        self.package_root = Path(self.temp_dir) / "test_package"
        
        # Create test repository
        self.repo_root.mkdir(parents=True)
        
        # Create test package structure
        self.package_root.mkdir(parents=True)
        (self.package_root / "cursor-rules" / "rules").mkdir(parents=True)
        (self.package_root / "cursor-rules" / "prompts").mkdir(parents=True)
        
        # Create test templates
        self._create_test_templates()
        
        # Create deployer
        self.deployer = CursorConfigDeployer(self.repo_root, self.package_root)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_templates(self):
        """Create test template files."""
        # Create shared rule template
        shared_template = self.package_root / "cursor-rules" / "rules" / "shared.mdc.jinja2"
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
        linux_template = self.package_root / "cursor-rules" / "rules" / "linux-dev.mdc.jinja2"
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
        prompt_template = self.package_root / "cursor-rules" / "prompts" / "test-prompt.md.jinja2"
        prompt_template.write_text("""# Test Prompt

This is a test prompt template.
Platform: {{ os }}
User: {{ user }}
""")
        
        # Create MCP config template
        mcp_template = self.package_root / "cursor-rules" / "mcp.json.jinja2"
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
    
    def test_initialization(self):
        """Test deployer initialization."""
        assert self.deployer.repo_root == self.repo_root
        assert self.deployer.package_root == self.package_root
        assert self.deployer.cursor_dir == self.repo_root / ".cursor"
        assert self.deployer.templates_dir == self.package_root / "cursor-rules"
    
    def test_detect_platform(self):
        """Test platform detection."""
        platform_info = self.deployer.detect_platform()
        
        assert "os" in platform_info
        assert "architecture" in platform_info
        assert "python_version" in platform_info
        assert "user" in platform_info
        assert "home" in platform_info
        assert "is_ci" in platform_info
    
    def test_deploy_basic(self):
        """Test basic deployment."""
        self.deployer.deploy()
        
        # Check that .cursor directory was created
        assert self.deployer.cursor_dir.exists()
        assert (self.deployer.cursor_dir / "rules").exists()
        assert (self.deployer.cursor_dir / "prompts").exists()
        
        # Check that shared rule was deployed
        shared_rule = self.deployer.cursor_dir / "rules" / "shared.mdc"
        assert shared_rule.exists()
        
        # Check that platform-specific rule was deployed
        platform_info = self.deployer.detect_platform()
        os_name = platform_info["os"]
        platform_rule = self.deployer.cursor_dir / "rules" / f"{os_name}-dev.mdc"
        assert platform_rule.exists()
        
        # Check that prompt was deployed
        prompt_file = self.deployer.cursor_dir / "prompts" / "test-prompt.md"
        assert prompt_file.exists()
        
        # Check that MCP config was deployed
        mcp_config = self.deployer.cursor_dir / "mcp.json"
        assert mcp_config.exists()
    
    def test_deploy_with_custom_rules(self):
        """Test deployment with custom rules."""
        # Create custom rule file
        custom_rule = Path(self.temp_dir) / "custom-rule.mdc"
        custom_rule.write_text("""---
title: Custom Rule
description: A custom rule for testing
---

# Custom Rule

This is a custom rule.
""")
        
        # Deploy with custom rules
        self.deployer.deploy(custom_rules=[custom_rule])
        
        # Check that custom rule was imported
        custom_dir = self.deployer.cursor_dir / "rules" / "custom"
        assert custom_dir.exists()
        
        imported_rule = custom_dir / "custom-rule.mdc"
        assert imported_rule.exists()
        assert imported_rule.read_text() == custom_rule.read_text()
    
    def test_deploy_opt_out(self):
        """Test deployment opt-out."""
        # Deploy with opt-out
        self.deployer.deploy(opt_out=True)
        
        # Check that .cursor directory was not created
        assert not self.deployer.cursor_dir.exists()
    
    def test_deploy_force(self):
        """Test deployment with force flag."""
        # Deploy once
        self.deployer.deploy()
        assert self.deployer.cursor_dir.exists()
        
        # Deploy again with force
        self.deployer.deploy(force=True)
        assert self.deployer.cursor_dir.exists()
    
    def test_deploy_existing_without_force(self):
        """Test deployment when .cursor already exists without force."""
        # Deploy once
        self.deployer.deploy()
        assert self.deployer.cursor_dir.exists()
        
        # Try to deploy again without force (should not overwrite)
        with patch('builtins.print') as mock_print:
            self.deployer.deploy(force=False)
            mock_print.assert_called_with("ℹ️  .cursor/ already exists. Use --force to overwrite.")
    
    def test_show_status(self):
        """Test status display."""
        # Deploy configuration
        self.deployer.deploy()
        
        # Show status
        with patch('builtins.print') as mock_print:
            self.deployer.show_status()
            # Check that status was printed
            assert mock_print.call_count > 0
    
    def test_dry_run(self):
        """Test dry run mode."""
        with patch('builtins.print') as mock_print:
            self.deployer.dry_run()
            # Check that dry run information was printed
            assert mock_print.call_count > 0
    
    def test_render_template(self):
        """Test template rendering."""
        # Create a simple template
        template_path = self.package_root / "cursor-rules" / "test-template.jinja2"
        template_path.write_text("Hello {{ user }} from {{ os }}!")
        
        # Render template
        output_path = self.deployer.cursor_dir / "test-output.txt"
        self.deployer.cursor_dir.mkdir(parents=True)
        
        platform_info = self.deployer.detect_platform()
        self.deployer._render_template(
            "test-template.jinja2",
            output_path,
            platform_info
        )
        
        # Check output
        assert output_path.exists()
        content = output_path.read_text()
        assert "Hello" in content
        assert platform_info["user"] in content
        assert platform_info["os"] in content


class TestPlatformDetector:
    """Test cases for PlatformDetector."""
    
    def test_detect_platform(self):
        """Test platform detection."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()
        
        assert "os" in platform_info
        assert "architecture" in platform_info
        assert "python_version" in platform_info
        assert "user" in platform_info
        assert "home" in platform_info
        assert "is_ci" in platform_info
    
    def test_get_rule_template_name(self):
        """Test rule template name selection."""
        detector = PlatformDetector()
        template_name = detector.get_rule_template_name()
        
        assert template_name in ["linux-dev", "macos-dev", "windows-dev", "ci-linux"]
    
    def test_get_mcp_command(self):
        """Test MCP command selection."""
        detector = PlatformDetector()
        command = detector.get_mcp_command()
        
        assert command in ["npx", "npx.cmd"]
    
    def test_is_development_environment(self):
        """Test development environment detection."""
        detector = PlatformDetector()
        is_dev = detector.is_development_environment()
        
        assert isinstance(is_dev, bool)
    
    def test_get_conan_home(self):
        """Test Conan home directory detection."""
        detector = PlatformDetector()
        conan_home = detector.get_conan_home()
        
        assert isinstance(conan_home, str)
        assert len(conan_home) > 0


class TestCursorConfig:
    """Test cases for CursorConfig."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cursor_dir = Path(self.temp_dir) / ".cursor"
        self.cursor_config = CursorConfig(self.cursor_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_directory_structure(self):
        """Test directory structure creation."""
        self.cursor_config.create_directory_structure()
        
        assert self.cursor_dir.exists()
        assert (self.cursor_dir / "rules").exists()
        assert (self.cursor_dir / "prompts").exists()
        assert (self.cursor_dir / "rules" / "custom").exists()
    
    def test_write_rule(self):
        """Test rule writing."""
        from mcp_orchestrator.cursor_config import CursorRule
        
        rule = CursorRule(
            title="Test Rule",
            description="A test rule",
            platform="test",
            content="# Test Rule\n\nThis is a test rule.",
            created="2024-01-01T00:00:00",
            user="testuser"
        )
        
        self.cursor_config.create_directory_structure()
        self.cursor_config.write_rule(rule, "test-rule")
        
        rule_file = self.cursor_dir / "rules" / "test-rule.mdc"
        assert rule_file.exists()
        
        content = rule_file.read_text()
        assert "Test Rule" in content
        assert "testuser" in content
    
    def test_write_prompt(self):
        """Test prompt writing."""
        self.cursor_config.create_directory_structure()
        self.cursor_config.write_prompt("Test Prompt", "This is a test prompt.", "test-prompt")
        
        prompt_file = self.cursor_dir / "prompts" / "test-prompt.md"
        assert prompt_file.exists()
        
        content = prompt_file.read_text()
        assert "# Test Prompt" in content
        assert "This is a test prompt." in content
    
    def test_write_mcp_config(self):
        """Test MCP configuration writing."""
        from mcp_orchestrator.cursor_config import MCPServerConfig
        
        servers = [
            MCPServerConfig(
                name="test-server",
                command="npx",
                args=["-y", "@test/server"],
                env={"PLATFORM": "test"},
                disabled=False
            )
        ]
        
        self.cursor_config.create_directory_structure()
        self.cursor_config.write_mcp_config(servers)
        
        mcp_file = self.cursor_dir / "mcp.json"
        assert mcp_file.exists()
        
        import json
        config = json.loads(mcp_file.read_text())
        assert "mcpServers" in config
        assert "test-server" in config["mcpServers"]
    
    def test_create_gitignore(self):
        """Test .gitignore creation."""
        self.cursor_config.create_directory_structure()
        self.cursor_config.create_gitignore()
        
        gitignore_file = self.cursor_dir / ".gitignore"
        assert gitignore_file.exists()
        
        content = gitignore_file.read_text()
        assert "rules/custom/" in content
        assert "*.log" in content
    
    def test_get_existing_rules(self):
        """Test getting existing rules."""
        self.cursor_config.create_directory_structure()
        
        # Create test rule files
        (self.cursor_dir / "rules" / "rule1.mdc").write_text("Rule 1")
        (self.cursor_dir / "rules" / "rule2.mdc").write_text("Rule 2")
        
        rules = self.cursor_config.get_existing_rules()
        assert "rule1" in rules
        assert "rule2" in rules
    
    def test_get_existing_prompts(self):
        """Test getting existing prompts."""
        self.cursor_config.create_directory_structure()
        
        # Create test prompt files
        (self.cursor_dir / "prompts" / "prompt1.md").write_text("Prompt 1")
        (self.cursor_dir / "prompts" / "prompt2.md").write_text("Prompt 2")
        
        prompts = self.cursor_config.get_existing_prompts()
        assert "prompt1" in prompts
        assert "prompt2" in prompts
    
    def test_has_mcp_config(self):
        """Test MCP configuration detection."""
        self.cursor_config.create_directory_structure()
        
        # Initially no MCP config
        assert not self.cursor_config.has_mcp_config()
        
        # Create MCP config
        (self.cursor_dir / "mcp.json").write_text('{"test": "config"}')
        assert self.cursor_config.has_mcp_config()
    
    def test_is_configured(self):
        """Test configuration detection."""
        # Initially not configured
        assert not self.cursor_config.is_configured()
        
        # Create directory structure
        self.cursor_config.create_directory_structure()
        
        # Still not configured (no rules or prompts)
        assert not self.cursor_config.is_configured()
        
        # Add a rule
        (self.cursor_dir / "rules" / "test.mdc").write_text("Test rule")
        assert self.cursor_config.is_configured()