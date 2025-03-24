"""
Integration tests for the prompt manager.

These tests verify that the prompt manager components work together properly.
"""

import os
import pytest
import tempfile
from pathlib import Path
import json

from mcp_project_orchestrator.core import MCPConfig
from mcp_project_orchestrator.prompt_manager import PromptManager
from mcp_project_orchestrator.prompt_manager import PromptTemplate
from mcp_project_orchestrator.prompt_manager import PromptLoader


class TestPromptManagerIntegration:
    """Integration tests for prompt manager components."""
    
    @pytest.fixture
    def temp_prompts_dir(self):
        """Create a temporary prompts directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_dir = Path(temp_dir) / "prompts"
            prompts_dir.mkdir(exist_ok=True)
            yield prompts_dir
    
    @pytest.fixture
    def config(self, temp_prompts_dir):
        """Create a test configuration."""
        config_data = {
            "name": "test-prompt-manager",
            "version": "0.1.0",
            "description": "Test Prompt Manager",
            "paths": {
                "prompts": str(temp_prompts_dir)
            }
        }
        
        config_file = temp_prompts_dir.parent / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)
            
        return MCPConfig(config_file=config_file)
    
    @pytest.fixture
    def sample_templates(self, temp_prompts_dir):
        """Create sample prompt templates."""
        templates = [
            {
                "name": "greeting",
                "description": "A simple greeting template",
                "template": "Hello, {{ name }}!",
                "variables": {
                    "name": {
                        "type": "string",
                        "description": "The name to greet"
                    }
                },
                "category": "general",
                "tags": ["greeting", "simple"]
            },
            {
                "name": "project-description",
                "description": "A template for describing projects",
                "template": "# {{ project_name }}\n\n{{ project_description }}\n\n## Features\n\n{{ features }}",
                "variables": {
                    "project_name": {
                        "type": "string",
                        "description": "The name of the project"
                    },
                    "project_description": {
                        "type": "string",
                        "description": "A brief description of the project"
                    },
                    "features": {
                        "type": "string",
                        "description": "Key features of the project"
                    }
                },
                "category": "documentation",
                "tags": ["project", "documentation"]
            }
        ]
        
        # Write templates to files
        for template in templates:
            template_file = temp_prompts_dir / f"{template['name']}.json"
            with open(template_file, "w") as f:
                json.dump(template, f)
                
        return templates
    
    @pytest.mark.asyncio
    async def test_prompt_loader_initialization(self, config, sample_templates):
        """Test that the prompt loader initializes properly."""
        loader = PromptLoader(config)
        await loader.initialize()
        
        # Check if templates were loaded
        assert "greeting" in loader.templates
        assert "project-description" in loader.templates
        
        # Check if categories and tags were extracted
        assert "general" in loader.categories
        assert "documentation" in loader.categories
        assert "greeting" in loader.tags
        assert "project" in loader.tags
        
    @pytest.mark.asyncio
    async def test_prompt_template_rendering(self, config, sample_templates):
        """Test that templates can be rendered properly."""
        loader = PromptLoader(config)
        await loader.initialize()
        
        greeting_template = loader.get_template("greeting")
        rendered = greeting_template.render({"name": "World"})
        assert rendered == "Hello, World!"
        
        project_template = loader.get_template("project-description")
        rendered = project_template.render({
            "project_name": "Test Project",
            "project_description": "A project for testing",
            "features": "- Feature 1\n- Feature 2"
        })
        assert "# Test Project" in rendered
        assert "A project for testing" in rendered
        assert "- Feature 1" in rendered
        assert "- Feature 2" in rendered
        
    @pytest.mark.asyncio
    async def test_prompt_manager_operations(self, config, sample_templates):
        """Test prompt manager operations."""
        manager = PromptManager(config)
        await manager.initialize()
        
        # Test loading template
        greeting = await manager.load_template("greeting")
        assert greeting is not None
        assert greeting.name == "greeting"
        
        # Test rendering template
        rendered = await manager.render_template("greeting", {"name": "World"})
        assert rendered == "Hello, World!"
        
        # Test creating a new template
        new_template = PromptTemplate(
            name="farewell",
            description="A farewell template",
            template="Goodbye, {{ name }}!",
            variables={
                "name": {
                    "type": "string",
                    "description": "The name to say goodbye to"
                }
            },
            category="general",
            tags=["farewell", "simple"]
        )
        
        await manager.create_template(new_template)
        
        # Test the new template was added
        farewell = await manager.load_template("farewell")
        assert farewell is not None
        assert farewell.name == "farewell"
        
        # Test rendering the new template
        rendered = await manager.render_template("farewell", {"name": "World"})
        assert rendered == "Goodbye, World!"
        
        # Test getting templates by category
        general_templates = manager.get_templates_by_category("general")
        assert len(general_templates) == 2
        assert "greeting" in [t.name for t in general_templates]
        assert "farewell" in [t.name for t in general_templates]
        
        # Test getting templates by tag
        simple_templates = manager.get_templates_by_tag("simple")
        assert len(simple_templates) == 2
        assert "greeting" in [t.name for t in simple_templates]
        assert "farewell" in [t.name for t in simple_templates]
        
        # Test deleting a template
        result = await manager.delete_template("greeting")
        assert result is True
        
        # Check if the template was deleted
        greeting = await manager.load_template("greeting")
        assert greeting is None 