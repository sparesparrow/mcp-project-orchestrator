"""Tests for the prompt management system."""

import pytest
from pathlib import Path

from mcp_project_orchestrator.prompts import (
    PromptManager,
    PromptTemplate,
    PromptCategory,
    PromptMetadata,
)

def test_prompt_metadata():
    """Test prompt metadata creation and conversion."""
    metadata = PromptMetadata(
        name="test-prompt",
        description="Test prompt",
        category=PromptCategory.SYSTEM,
        version="1.0.0",
        author="Test Author",
        tags=["test", "system"],
        variables={"var1": "desc1", "var2": "desc2"},
    )
    
    # Test to_dict
    data = metadata.to_dict()
    assert data["name"] == "test-prompt"
    assert data["category"] == "system"
    
    # Test from_dict
    new_metadata = PromptMetadata.from_dict(data)
    assert new_metadata.name == metadata.name
    assert new_metadata.category == metadata.category

def test_prompt_template():
    """Test prompt template creation and rendering."""
    template = PromptTemplate(
        metadata=PromptMetadata(
            name="test-prompt",
            description="Test prompt",
            category=PromptCategory.SYSTEM,
        ),
        content="Hello {{ name }}! Welcome to {{ project }}.",
    )
    
    # Test variable substitution
    rendered = template.render({
        "name": "User",
        "project": "MCP",
    })
    assert rendered == "Hello User! Welcome to MCP."
    
    # Test missing variable
    with pytest.raises(KeyError):
        template.render({"name": "User"})

def test_prompt_manager(prompt_manager, temp_dir):
    """Test prompt manager functionality."""
    # Create test prompt
    prompt_dir = temp_dir / "prompts"
    prompt_dir.mkdir(parents=True)
    
    prompt_file = prompt_dir / "test-prompt.json"
    prompt_file.write_text("""
    {
        "metadata": {
            "name": "test-prompt",
            "description": "Test prompt",
            "category": "system",
            "version": "1.0.0",
            "author": "Test Author",
            "tags": ["test", "system"],
            "variables": {
                "name": "User name",
                "project": "Project name"
            }
        },
        "content": "Hello {{ name }}! Welcome to {{ project }}."
    }
    """)
    
    # Load prompts
    prompt_manager.discover_prompts()
    
    # List prompts
    all_prompts = prompt_manager.list_prompts()
    assert "test-prompt" in all_prompts
    
    # Get specific prompts
    system_prompts = prompt_manager.list_prompts(PromptCategory.SYSTEM)
    assert "test-prompt" in system_prompts
    
    # Get prompt
    prompt = prompt_manager.get_prompt("test-prompt")
    assert prompt is not None
    assert prompt.metadata.name == "test-prompt"
    assert prompt.metadata.category == PromptCategory.SYSTEM
    
    # Render prompt
    rendered = prompt_manager.render_prompt("test-prompt", {
        "name": "User",
        "project": "MCP",
    })
    assert rendered == "Hello User! Welcome to MCP."

def test_prompt_validation(prompt_manager):
    """Test prompt validation."""
    # Invalid prompt (missing required fields)
    metadata = PromptMetadata(
        name="invalid-prompt",
        description="Invalid prompt",
        category=PromptCategory.SYSTEM,
    )
    template = PromptTemplate(metadata=metadata, content="")
    assert not template.validate()
    
    # Valid prompt
    metadata = PromptMetadata(
        name="valid-prompt",
        description="Valid prompt",
        category=PromptCategory.SYSTEM,
        version="1.0.0",
        author="Test Author",
        tags=["test"],
        variables={"var1": "desc1"},
    )
    template = PromptTemplate(metadata=metadata, content="Test {{ var1 }}")
    assert template.validate()

def test_prompt_save_load(prompt_manager, temp_dir):
    """Test saving and loading prompts."""
    # Create prompt
    metadata = PromptMetadata(
        name="save-test",
        description="Save test prompt",
        category=PromptCategory.SYSTEM,
        version="1.0.0",
        author="Test Author",
        tags=["test"],
        variables={"var1": "desc1"},
    )
    template = PromptTemplate(metadata=metadata, content="Test {{ var1 }}")
    
    # Save prompt
    prompt_manager.save_prompt(template)
    
    # Load prompt
    loaded = prompt_manager.get_prompt("save-test")
    assert loaded is not None
    assert loaded.metadata.name == template.metadata.name
    assert loaded.content == template.content 