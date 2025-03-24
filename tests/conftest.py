"""Pytest configuration and fixtures."""

import os
import shutil
import tempfile
from pathlib import Path
import pytest
import json

from mcp_project_orchestrator.core import Config
from mcp_project_orchestrator.templates import TemplateManager
from mcp_project_orchestrator.prompt_manager import PromptManager
from mcp_project_orchestrator.mermaid import MermaidGenerator, MermaidRenderer

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    config = Config()
    config.workspace_dir = temp_dir / "workspace"
    config.templates_dir = temp_dir / "templates"
    config.resources_dir = temp_dir / "resources"
    config.prompt_templates_dir = temp_dir / "prompts"
    config.mermaid_output_dir = temp_dir / "diagrams"
    
    # Create directories
    config.workspace_dir.mkdir(parents=True)
    config.templates_dir.mkdir(parents=True)
    config.resources_dir.mkdir(parents=True)
    config.prompt_templates_dir.mkdir(parents=True)
    config.mermaid_output_dir.mkdir(parents=True)
    
    return config

@pytest.fixture
def template_manager(test_config):
    """Create a template manager instance."""
    return TemplateManager(test_config.templates_dir)

@pytest.fixture
def prompt_manager(test_config):
    """Create a prompt manager instance."""
    manager = PromptManager(test_config)
    return manager

@pytest.fixture
def mermaid_generator(test_config):
    """Create a Mermaid generator instance."""
    return MermaidGenerator(test_config)

@pytest.fixture
def mermaid_renderer(test_config):
    """Create a Mermaid renderer instance."""
    return MermaidRenderer(test_config)

@pytest.fixture
def sample_project_template(temp_dir):
    """Create a sample project template for testing."""
    template_dir = temp_dir / "templates" / "sample-project"
    template_dir.mkdir(parents=True)
    
    # Create template.json
    template_json = {
        "name": "sample-project",
        "description": "A sample project template for testing",
        "type": "project",
        "version": "1.0.0",
        "variables": {
            "project_name": "Name of the project",
            "project_description": "Project description",
            "author_name": "Author's name",
            "author_email": "Author's email"
        }
    }
    
    with open(template_dir / "template.json", "w") as f:
        json.dump(template_json, f, indent=2)
        
    # Create sample files
    files_dir = template_dir / "files"
    files_dir.mkdir()
    
    with open(files_dir / "README.md", "w") as f:
        f.write("# {{ project_name }}\n\n{{ project_description }}")
        
    with open(files_dir / "pyproject.toml", "w") as f:
        f.write('[project]\nname = "{{ project_name }}"\nauthor = "{{ author_name }}"')
        
    (files_dir / "src").mkdir()
    (files_dir / "tests").mkdir()
    
    return template_dir

@pytest.fixture
def sample_component_template(temp_dir):
    """Create a sample component template for testing."""
    template_dir = temp_dir / "templates" / "sample-component"
    template_dir.mkdir(parents=True)
    
    # Create template.json
    template_json = {
        "name": "sample-component",
        "description": "A sample component template for testing",
        "type": "component",
        "version": "1.0.0",
        "variables": {
            "component_name": "Name of the component",
            "component_description": "Component description"
        }
    }
    
    with open(template_dir / "template.json", "w") as f:
        json.dump(template_json, f, indent=2)
        
    # Create sample files
    files_dir = template_dir / "files"
    files_dir.mkdir()
    
    with open(files_dir / "{{ component_name }}.py", "w") as f:
        f.write('"""{{ component_description }}"""\n\nclass {{ component_name }}:\n    pass')
        
    return template_dir 