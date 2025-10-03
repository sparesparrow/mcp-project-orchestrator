"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import json
import yaml

from mcp_project_orchestrator.core import MCPConfig, Config


def test_config_creation():
    """Test basic config creation."""
    config = MCPConfig()
    assert config.settings is not None
    assert config.settings.workspace_dir == Path.cwd()
    assert config.settings.host == "localhost"
    assert config.settings.port == 8000


def test_config_alias():
    """Test that Config is an alias for MCPConfig."""
    assert Config is MCPConfig
    config = Config()
    assert isinstance(config, MCPConfig)


def test_config_path_helpers(tmp_path):
    """Test configuration path helper methods."""
    config = MCPConfig()
    config.settings.workspace_dir = tmp_path
    config.settings.templates_dir = tmp_path / "templates"
    config.settings.prompts_dir = tmp_path / "prompts"
    config.settings.resources_dir = tmp_path / "resources"
    
    # Test path helpers
    workspace_path = config.get_workspace_path("test", "file.txt")
    assert workspace_path == tmp_path / "test" / "file.txt"
    
    template_path = config.get_template_path("template.json")
    assert template_path == tmp_path / "templates" / "template.json"
    
    prompt_path = config.get_prompt_path("prompt.json")
    assert prompt_path == tmp_path / "prompts" / "prompt.json"
    
    resource_path = config.get_resource_path("resource.txt")
    assert resource_path == tmp_path / "resources" / "resource.txt"


def test_config_json_loading(tmp_path):
    """Test loading configuration from JSON file."""
    config_file = tmp_path / "config.json"
    config_data = {
        "workspace_dir": str(tmp_path / "workspace"),
        "templates_dir": str(tmp_path / "templates"),
        "prompts_dir": str(tmp_path / "prompts"),
        "host": "0.0.0.0",
        "port": 9000,
        "debug": True
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    config = MCPConfig(config_path=config_file)
    config.load_config()
    
    assert config.settings.host == "0.0.0.0"
    assert config.settings.port == 9000
    assert config.settings.debug is True


def test_config_yaml_loading(tmp_path):
    """Test loading configuration from YAML file."""
    config_file = tmp_path / "config.yml"
    config_data = {
        "workspace_dir": str(tmp_path / "workspace"),
        "host": "127.0.0.1",
        "port": 8080
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    config = MCPConfig(config_path=config_file)
    config.load_config()
    
    assert config.settings.host == "127.0.0.1"
    assert config.settings.port == 8080


def test_config_directory_creation(tmp_path):
    """Test that config creates required directories."""
    config = MCPConfig()
    config.settings.workspace_dir = tmp_path / "workspace"
    config.settings.templates_dir = tmp_path / "templates"
    config.settings.prompts_dir = tmp_path / "prompts"
    config.settings.resources_dir = tmp_path / "resources"
    config.settings.output_dir = tmp_path / "output"
    
    config._create_directories()
    
    assert config.settings.workspace_dir.exists()
    assert config.settings.templates_dir.exists()
    assert config.settings.prompts_dir.exists()
    assert config.settings.resources_dir.exists()
    assert config.settings.output_dir.exists()


def test_config_invalid_file_format(tmp_path):
    """Test error handling for invalid config file format."""
    config_file = tmp_path / "config.txt"
    config_file.write_text("invalid config")
    
    config = MCPConfig(config_path=config_file)
    
    with pytest.raises(ValueError, match="Unsupported config file format"):
        config.load_config()


def test_config_settings_defaults():
    """Test default settings values."""
    config = MCPConfig()
    
    assert config.settings.host == "localhost"
    assert config.settings.port == 8000
    assert config.settings.debug is False
    assert config.settings.template_extensions[".py"] == "python"
    assert config.settings.template_extensions[".js"] == "javascript"
