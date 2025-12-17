"""Tests for the template system."""

import pytest
from pathlib import Path

from mcp_project_orchestrator.templates import (
    TemplateType,
    TemplateCategory,
    TemplateMetadata,
    TemplateFile,
    ProjectTemplate,
    ComponentTemplate,
)

def test_template_metadata():
    """Test template metadata creation and conversion."""
    metadata = TemplateMetadata(
        name="test-template",
        description="Test template",
        type=TemplateType.PROJECT,
        category=TemplateCategory.API,
        version="1.0.0",
        author="Test Author",
        tags=["test", "api"],
        dependencies=["dep1", "dep2"],
        variables={"var1": "desc1", "var2": "desc2"},
    )
    
    # Test to_dict
    data = metadata.to_dict()
    assert data["name"] == "test-template"
    assert data["type"] == "project"
    assert data["category"] == "api"
    
    # Test from_dict
    new_metadata = TemplateMetadata.from_dict(data)
    assert new_metadata.name == metadata.name
    assert new_metadata.type == metadata.type
    assert new_metadata.category == metadata.category

def test_template_file():
    """Test template file creation and conversion."""
    file = TemplateFile(
        path="test.py",
        content="print('Hello')",
        is_executable=True,
        variables={"var1": "desc1"},
    )
    
    # Test to_dict
    data = file.to_dict()
    assert data["path"] == "test.py"
    assert data["content"] == "print('Hello')"
    assert data["is_executable"] is True
    
    # Test from_dict
    new_file = TemplateFile.from_dict(data)
    assert new_file.path == file.path
    assert new_file.content == file.content
    assert new_file.is_executable == file.is_executable

def test_project_template(sample_project_template, temp_dir):
    """Test project template functionality."""
    # Load template
    metadata = TemplateMetadata.from_dict({
        "name": "test-project",
        "description": "Test project",
        "type": "project",
    })
    template = ProjectTemplate(metadata)
    
    # Add files
    template.add_file(TemplateFile(
        path="README.md",
        content="# {{ project_name }}\n{{ project_description }}",
    ))
    template.add_file(TemplateFile(
        path="src/main.py",
        content="print('{{ project_name }}')",
    ))
    
    # Set variables
    template.set_variable("project_name", "Test Project")
    template.set_variable("project_description", "A test project")
    template.set_variable("author_name", "Test Author")
    template.set_variable("author_email", "test@example.com")
    
    # Apply template
    output_dir = temp_dir / "output"
    template.apply(output_dir)
    
    # Verify output
    assert (output_dir / "Test Project").exists()
    assert (output_dir / "Test Project" / "README.md").exists()
    assert (output_dir / "Test Project" / "src" / "main.py").exists()

def test_component_template(sample_component_template, temp_dir):
    """Test component template functionality."""
    # Load template
    metadata = TemplateMetadata.from_dict({
        "name": "test-component",
        "description": "Test component",
        "type": "component",
    })
    template = ComponentTemplate(metadata)
    
    # Add file
    template.add_file(TemplateFile(
        path="{{ component_name }}.py",
        content="class {{ component_name }}:\n    pass",
    ))
    
    # Set variables
    template.set_variable("component_name", "TestComponent")
    template.set_variable("component_description", "A test component")
    
    # Apply template
    output_dir = temp_dir / "output"
    template.apply(output_dir)
    
    # Verify output
    assert (output_dir / "TestComponent.py").exists()

def test_template_manager(template_manager, sample_project_template, sample_component_template):
    """Test template manager functionality."""
    # Discover templates
    template_manager.discover_templates()
    
    # List templates
    all_templates = template_manager.list_templates()
    assert "sample-project" in all_templates
    assert "sample-component" in all_templates
    
    # Get specific templates
    project_templates = template_manager.list_templates(TemplateType.PROJECT)
    assert "sample-project" in project_templates
    assert "sample-component" not in project_templates
    
    # Get template
    template = template_manager.get_template("sample-project")
    assert template is not None
    assert template.metadata.name == "sample-project"
    assert template.metadata.type == TemplateType.PROJECT

def test_template_validation(template_manager):
    """Test template validation."""
    # Invalid project template (missing required files)
    metadata = TemplateMetadata(
        name="invalid-project",
        description="Invalid project",
        type=TemplateType.PROJECT,
    )
    template = ProjectTemplate(metadata)
    assert not template.validate()
    
    # Invalid component template (no files)
    metadata = TemplateMetadata(
        name="invalid-component",
        description="Invalid component",
        type=TemplateType.COMPONENT,
    )
    template = ComponentTemplate(metadata)
    assert not template.validate()
    
    # Valid project template
    metadata = TemplateMetadata(
        name="valid-project",
        description="Valid project",
        type=TemplateType.PROJECT,
    )
    template = ProjectTemplate(metadata)
    template.add_file(TemplateFile(path="README.md", content=""))
    template.add_file(TemplateFile(path="pyproject.toml", content=""))
    template.add_file(TemplateFile(path="src/main.py", content=""))
    template.add_file(TemplateFile(path="tests/test_main.py", content=""))
    
    template.set_variable("project_name", "Test")
    template.set_variable("project_description", "Test")
    template.set_variable("author_name", "Test")
    template.set_variable("author_email", "test@example.com")
    
    assert template.validate() 