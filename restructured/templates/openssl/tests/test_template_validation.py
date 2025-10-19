"""
Tests for template rendering and JSON schema validation.

This module contains tests for Jinja2 template rendering and
JSON configuration schema validation.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from mcp_orchestrator.cursor_deployer import CursorConfigDeployer
from mcp_orchestrator.yaml_validator import YAMLFrontmatterValidator
from mcp_orchestrator.env_config import EnvironmentConfig


class TestTemplateRendering:
    """Test cases for Jinja2 template rendering."""
    
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
title: {{ title }}
description: {{ description }}
created: {{ timestamp }}
platform: {{ platform }}
user: {{ user }}
---

# {{ title }}

This is a test shared rule template.
Platform: {{ os }}
User: {{ user }}
Python: {{ python_version }}
""")
        
        # Create MCP config template
        mcp_template = self.package_root / "cursor-rules" / "mcp.json.jinja2"
        mcp_template.write_text("""{
  "mcpServers": {
    "test-server": {
      "command": "{% if os == 'windows' %}npx.cmd{% else %}npx{% endif %}",
      "args": ["-y", "@test/server"],
      "env": {
        "PLATFORM": "{{ os }}",
        "USER": "{{ user }}",
        "HOME": "{{ home }}",
        "CI": {{ is_ci | lower }}
      }
    }
  },
  "platform": {
    "os": "{{ os }}",
    "architecture": "{{ architecture }}",
    "pythonVersion": "{{ python_version }}"
  }
}
""")
    
    def test_template_rendering_basic(self):
        """Test basic template rendering."""
        platform_info = self.deployer.detect_platform()
        
        # Test shared rule template
        content = self.deployer._render_template_content(
            "rules/shared.mdc.jinja2",
            platform_info
        )
        
        assert "title: Shared Rules" in content
        assert f"Platform: {platform_info['os']}" in content
        assert f"User: {platform_info['user']}" in content
        assert f"Python: {platform_info['python_version']}" in content
    
    def test_template_rendering_with_custom_variables(self):
        """Test template rendering with custom variables."""
        platform_info = self.deployer.detect_platform()
        platform_info.update({
            "title": "Custom Test Rules",
            "description": "Custom test description",
            "platform": "test"
        })
        
        content = self.deployer._render_template_content(
            "rules/shared.mdc.jinja2",
            platform_info
        )
        
        assert "title: Custom Test Rules" in content
        assert "description: Custom test description" in content
        assert "platform: test" in content
    
    def test_mcp_config_rendering(self):
        """Test MCP configuration template rendering."""
        platform_info = self.deployer.detect_platform()
        
        content = self.deployer._render_template_content(
            "mcp.json.jinja2",
            platform_info
        )
        
        # Parse as JSON to validate
        config = json.loads(content)
        
        assert "mcpServers" in config
        assert "test-server" in config["mcpServers"]
        assert "platform" in config
        
        # Check platform-specific command
        expected_command = "npx.cmd" if platform_info["os"] == "windows" else "npx"
        assert config["mcpServers"]["test-server"]["command"] == expected_command
        
        # Check environment variables
        env = config["mcpServers"]["test-server"]["env"]
        assert env["PLATFORM"] == platform_info["os"]
        assert env["USER"] == platform_info["user"]
        assert env["HOME"] == platform_info["home"]
        assert env["CI"] == platform_info["is_ci"]
    
    def test_template_rendering_error_handling(self):
        """Test template rendering error handling."""
        # Create invalid template
        invalid_template = self.package_root / "cursor-rules" / "invalid.jinja2"
        invalid_template.write_text("{{ invalid_variable_that_does_not_exist }}")
        
        with pytest.raises(Exception):
            self.deployer._render_template_content(
                "invalid.jinja2",
                {"os": "linux"}
            )
    
    def test_template_rendering_with_filters(self):
        """Test template rendering with Jinja2 filters."""
        platform_info = self.deployer.detect_platform()
        
        # Test boolean filter
        content = self.deployer._render_template_content(
            "mcp.json.jinja2",
            platform_info
        )
        
        config = json.loads(content)
        env = config["mcpServers"]["test-server"]["env"]
        assert isinstance(env["CI"], bool)
        assert env["CI"] == platform_info["is_ci"]


class TestJSONSchemaValidation:
    """Test cases for JSON configuration schema validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "test_repo"
        self.package_root = Path(self.temp_dir) / "test_package"
        
        # Create test repository
        self.repo_root.mkdir(parents=True)
        
        # Create test package structure
        self.package_root.mkdir(parents=True)
        (self.package_root / "cursor-rules").mkdir(parents=True)
        
        # Create test MCP template
        self._create_mcp_template()
        
        # Create deployer
        self.deployer = CursorConfigDeployer(self.repo_root, self.package_root)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_mcp_template(self):
        """Create MCP configuration template."""
        mcp_template = self.package_root / "cursor-rules" / "mcp.json.jinja2"
        mcp_template.write_text("""{
  "mcpServers": {
    "openssl-context": {
      "command": "{% if os == 'windows' %}npx.cmd{% else %}npx{% endif %}",
      "args": ["-y", "@sparesparrow/mcp-openssl-context"],
      "env": {
        "OPENSSL_PROJECT_ROOT": "{{ repo_root }}",
        "CONAN_USER_HOME": "{{ home }}/.conan2",
        "PLATFORM": "{{ os }}",
        "ARCHITECTURE": "{{ architecture }}",
        "PYTHON_VERSION": "{{ python_version }}",
        "USER": "{{ user }}"
      }
    },
    "build-intelligence": {
      "command": "{% if os == 'windows' %}npx.cmd{% else %}npx{% endif %}",
      "args": ["-y", "@sparesparrow/mcp-build-intelligence"],
      "env": {
        "OPENSSL_PROJECT_ROOT": "{{ repo_root }}",
        "PLATFORM": "{{ os }}",
        "ARCHITECTURE": "{{ architecture }}",
        "BUILD_TYPE": "{% if is_ci %}release{% else %}debug{% endif %}",
        "CONAN_USER_HOME": "{{ home }}/.conan2"
      }
    }
  },
  "globalShortcut": "Ctrl+Shift+.",
  "logging": {
    "level": "{% if is_ci %}error{% else %}info{% endif %}",
    "file": "{{ repo_root }}/.cursor/cursor.log",
    "maxSize": "10MB",
    "maxFiles": 5
  },
  "features": {
    "autoComplete": true,
    "syntaxHighlighting": true,
    "errorChecking": true,
    "codeFormatting": true,
    "intelligentSuggestions": true
  },
  "platform": {
    "os": "{{ os }}",
    "architecture": "{{ architecture }}",
    "pythonVersion": "{{ python_version }}",
    "user": "{{ user }}",
    "home": "{{ home }}",
    "ciEnvironment": {{ is_ci }},
    "timestamp": "{{ timestamp }}"
  }
}
""")
    
    def test_mcp_config_schema_validation(self):
        """Test MCP configuration JSON schema validation."""
        platform_info = self.deployer.detect_platform()
        platform_info["repo_root"] = str(self.repo_root)
        
        # Render template
        content = self.deployer._render_template_content(
            "mcp.json.jinja2",
            platform_info
        )
        
        # Parse as JSON
        config = json.loads(content)
        
        # Validate schema
        self._validate_mcp_config_schema(config)
    
    def _validate_mcp_config_schema(self, config: dict):
        """Validate MCP configuration schema."""
        # Check required top-level fields
        required_fields = ["mcpServers", "globalShortcut", "logging", "features", "platform"]
        for field in required_fields:
            assert field in config, f"Missing required field: {field}"
        
        # Validate mcpServers
        mcp_servers = config["mcpServers"]
        assert isinstance(mcp_servers, dict), "mcpServers must be a dictionary"
        
        for server_name, server_config in mcp_servers.items():
            assert isinstance(server_config, dict), f"Server {server_name} config must be a dictionary"
            
            # Check required server fields
            required_server_fields = ["command", "args", "env"]
            for field in required_server_fields:
                assert field in server_config, f"Server {server_name} missing required field: {field}"
            
            # Validate command
            assert isinstance(server_config["command"], str), f"Server {server_name} command must be a string"
            assert server_config["command"] in ["npx", "npx.cmd"], f"Server {server_name} has invalid command"
            
            # Validate args
            assert isinstance(server_config["args"], list), f"Server {server_name} args must be a list"
            
            # Validate env
            assert isinstance(server_config["env"], dict), f"Server {server_name} env must be a dictionary"
        
        # Validate logging
        logging = config["logging"]
        assert "level" in logging, "Logging missing level field"
        assert logging["level"] in ["error", "info", "debug", "warn"], "Invalid logging level"
        
        # Validate features
        features = config["features"]
        boolean_features = ["autoComplete", "syntaxHighlighting", "errorChecking", "codeFormatting", "intelligentSuggestions"]
        for feature in boolean_features:
            assert feature in features, f"Missing feature: {feature}"
            assert isinstance(features[feature], bool), f"Feature {feature} must be boolean"
        
        # Validate platform
        platform = config["platform"]
        required_platform_fields = ["os", "architecture", "pythonVersion", "user", "home", "ciEnvironment", "timestamp"]
        for field in required_platform_fields:
            assert field in platform, f"Platform missing required field: {field}"
    
    def test_mcp_config_rendering_consistency(self):
        """Test that MCP configuration rendering is consistent across platforms."""
        platforms = [
            {"os": "linux", "is_ci": False},
            {"os": "macos", "is_ci": False},
            {"os": "windows", "is_ci": False},
            {"os": "linux", "is_ci": True},
        ]
        
        for platform_info in platforms:
            platform_info.update({
                "architecture": "x86_64",
                "python_version": "3.9.0",
                "user": "testuser",
                "home": "/home/testuser",
                "timestamp": "2024-01-01T00:00:00",
                "repo_root": str(self.repo_root)
            })
            
            # Render template
            content = self.deployer._render_template_content(
                "mcp.json.jinja2",
                platform_info
            )
            
            # Parse as JSON
            config = json.loads(content)
            
            # Validate schema
            self._validate_mcp_config_schema(config)
            
            # Check platform-specific values
            assert config["platform"]["os"] == platform_info["os"]
            assert config["platform"]["ciEnvironment"] == platform_info["is_ci"]
            
            # Check command based on OS
            expected_command = "npx.cmd" if platform_info["os"] == "windows" else "npx"
            for server_config in config["mcpServers"].values():
                assert server_config["command"] == expected_command


class TestYAMLFrontmatterValidation:
    """Test cases for YAML frontmatter validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = YAMLFrontmatterValidator()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_valid_frontmatter(self):
        """Test validation of valid frontmatter."""
        # Create valid .mdc file
        mdc_file = Path(self.temp_dir) / "valid.mdc"
        mdc_file.write_text("""---
title: Test Rule
description: A test rule for validation
created: 2024-01-01T00:00:00
platform: linux
user: testuser
---

# Test Rule

This is a test rule.
""")
        
        result = self.validator.validate_file(mdc_file)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.frontmatter is not None
        assert result.frontmatter["title"] == "Test Rule"
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        # Create .mdc file with missing required fields
        mdc_file = Path(self.temp_dir) / "invalid.mdc"
        mdc_file.write_text("""---
title: Test Rule
---

# Test Rule

This is a test rule.
""")
        
        result = self.validator.validate_file(mdc_file)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("Missing required field" in error for error in result.errors)
    
    def test_invalid_yaml_syntax(self):
        """Test validation with invalid YAML syntax."""
        # Create .mdc file with invalid YAML
        mdc_file = Path(self.temp_dir) / "invalid_yaml.mdc"
        mdc_file.write_text("""---
title: Test Rule
description: A test rule
created: 2024-01-01T00:00:00
platform: linux
user: testuser
invalid_yaml: [unclosed list
---

# Test Rule

This is a test rule.
""")
        
        result = self.validator.validate_file(mdc_file)
        
        assert not result.is_valid
        assert any("Invalid YAML syntax" in error for error in result.errors)
    
    def test_invalid_platform(self):
        """Test validation with invalid platform."""
        # Create .mdc file with invalid platform
        mdc_file = Path(self.temp_dir) / "invalid_platform.mdc"
        mdc_file.write_text("""---
title: Test Rule
description: A test rule
created: 2024-01-01T00:00:00
platform: invalid_platform
user: testuser
---

# Test Rule

This is a test rule.
""")
        
        result = self.validator.validate_file(mdc_file)
        
        assert not result.is_valid
        assert any("Invalid platform" in error for error in result.errors)
    
    def test_no_frontmatter(self):
        """Test validation with no frontmatter."""
        # Create .mdc file without frontmatter
        mdc_file = Path(self.temp_dir) / "no_frontmatter.mdc"
        mdc_file.write_text("""# Test Rule

This is a test rule without frontmatter.
""")
        
        result = self.validator.validate_file(mdc_file)
        
        assert not result.is_valid
        assert any("No YAML frontmatter found" in error for error in result.errors)


class TestEnvironmentConfiguration:
    """Test cases for environment configuration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.env_config = EnvironmentConfig()
    
    def test_get_conan_home_fallback(self):
        """Test Conan home directory fallback."""
        # Clear cache
        self.env_config._cache.clear()
        
        # Test with environment variable set
        with patch.dict(os.environ, {"CONAN_USER_HOME": "/custom/conan/home"}):
            conan_home = self.env_config.get_conan_home()
            assert conan_home == "/custom/conan/home"
        
        # Test fallback
        with patch.dict(os.environ, {}, clear=True):
            conan_home = self.env_config.get_conan_home()
            assert conan_home.endswith(".conan2")
    
    def test_validate_required_openssl(self):
        """Test validation of required variables for OpenSSL project."""
        # Test with all required variables
        with patch.dict(os.environ, {
            "CONAN_USER_HOME": "/test/conan",
            "OPENSSL_ROOT_DIR": "/test/openssl"
        }):
            is_valid, missing = self.env_config.validate_required("openssl")
            assert is_valid
            assert len(missing) == 0
        
        # Test with missing variables
        with patch.dict(os.environ, {}, clear=True):
            is_valid, missing = self.env_config.validate_required("openssl")
            assert not is_valid
            assert "CONAN_USER_HOME" in missing
            assert "OPENSSL_ROOT_DIR" in missing
    
    def test_get_validation_errors(self):
        """Test getting validation error messages."""
        with patch.dict(os.environ, {}, clear=True):
            errors = self.env_config.get_validation_errors("openssl")
            assert len(errors) > 0
            assert any("Missing required environment variables" in error for error in errors)
            assert any("CONAN_USER_HOME" in error for error in errors)
            assert any("OPENSSL_ROOT_DIR" in error for error in errors)


# Import os for patching
import os