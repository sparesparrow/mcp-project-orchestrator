"""
Prompt manager for MCP Project Orchestrator.

This module provides the main prompt management functionality,
orchestrating template loading, rendering, and caching.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import asyncio
import json

from ..core import Config
from .template import PromptTemplate, PromptCategory
from .loader import PromptLoader


class PromptManager:
    """Main class for managing prompt templates."""
    
    def __init__(self, config: Config):
        """Initialize the prompt manager.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.loader = PromptLoader(config)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._templates: Dict[str, PromptTemplate] = {}
        
    async def initialize(self) -> None:
        """Initialize the prompt manager.
        
        Initializes the template loader and loads initial templates.
        """
        await self.loader.initialize()
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.loader.cleanup()
        self.cache.clear()
        
    async def load_template(self, name: str) -> Optional[PromptTemplate]:
        """Load a template by name.
        
        Args:
            name: Name of the template to load
            
        Returns:
            Loaded template or None if not found
        """
        # Check cache first
        if name in self.cache:
            return PromptTemplate(**self.cache[name])
            
        # Try loading from loader
        template = self.loader.get_template(name)
        if template:
            self.cache[name] = template.to_dict()
            
        return template
        
    async def render_template(
        self, name: str, variables: Dict[str, Any]
    ) -> Optional[str]:
        """Render a template with variables.
        
        Args:
            name: Name of the template to render
            variables: Variables to use in rendering
            
        Returns:
            Rendered template string or None if template not found
            
        Raises:
            KeyError: If required variables are missing
        """
        template = await self.load_template(name)
        if not template:
            return None
            
        return template.render(variables)
        
    async def create_template(
        self, template: PromptTemplate, save: bool = True
    ) -> None:
        """Create a new template.
        
        Args:
            template: Template to create
            save: Whether to save the template to disk
            
        Raises:
            ValueError: If template validation fails
            FileExistsError: If template with same name exists
        """
        template.validate()
        
        if template.name in self.loader.templates:
            raise FileExistsError(
                f"Template already exists: {template.name}"
            )
            
        if save:
            path = self.config.prompt_templates_dir / f"{template.name}.json"
            template.save(path)
            
        self.loader.templates[template.name] = template
        self.cache[template.name] = template.to_dict()
        
        if template.category:
            self.loader.categories.add(template.category)
        self.loader.tags.update(template.tags)
        
    async def update_template(
        self, name: str, updates: Dict[str, Any], save: bool = True
    ) -> Optional[PromptTemplate]:
        """Update an existing template.
        
        Args:
            name: Name of the template to update
            updates: Dictionary of fields to update
            save: Whether to save changes to disk
            
        Returns:
            Updated template or None if not found
            
        Raises:
            ValueError: If template validation fails
        """
        template = await self.load_template(name)
        if not template:
            return None
            
        # Update template fields
        template_dict = template.to_dict()
        template_dict.update(updates)
        
        # Create new template instance with updates
        updated = PromptTemplate(**template_dict)
        updated.validate()
        
        # Save if requested
        if save:
            path = self.config.prompt_templates_dir / f"{name}.json"
            updated.save(path)
            
        # Update internal state
        self.loader.templates[name] = updated
        self.cache[name] = updated.to_dict()
        
        # Update categories and tags
        if updated.category:
            self.loader.categories.add(updated.category)
        self.loader.tags.update(updated.tags)
        
        return updated
        
    async def delete_template(self, name: str) -> bool:
        """Delete a template.
        
        Args:
            name: Name of the template to delete
            
        Returns:
            True if template was deleted, False if not found
        """
        if name not in self.loader.templates:
            return False
            
        # Remove from disk
        path = self.config.prompt_templates_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            
        # Remove from internal state
        template = self.loader.templates.pop(name)
        self.cache.pop(name, None)
        
        # Update categories and tags
        if template.category:
            remaining_categories = {
                t.category for t in self.loader.templates.values()
                if t.category
            }
            self.loader.categories = remaining_categories
            
        remaining_tags = set()
        for t in self.loader.templates.values():
            remaining_tags.update(t.tags)
        self.loader.tags = remaining_tags
        
        return True
        
    def get_all_templates(self) -> List[PromptTemplate]:
        """Get all available templates.
        
        Returns:
            List of all templates
        """
        return list(self.loader.templates.values())
        
    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """Get all templates in a category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of templates in the category
        """
        return self.loader.get_templates_by_category(category)
        
    def get_templates_by_tag(self, tag: str) -> List[PromptTemplate]:
        """Get all templates with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of templates with the tag
        """
        return self.loader.get_templates_by_tag(tag)
        
    def get_all_categories(self) -> List[str]:
        """Get all available categories.
        
        Returns:
            List of category names
        """
        return self.loader.get_all_categories()
        
    def get_all_tags(self) -> List[str]:
        """Get all available tags.
        
        Returns:
            List of tag names
        """
        return self.loader.get_all_tags()
    
    def discover_prompts(self) -> None:
        """Discover and load all prompt templates from the prompts directory."""
        prompts_dir = self.config.settings.prompts_dir
        if not prompts_dir.exists():
            return
        
        for prompt_file in prompts_dir.rglob("*.json"):
            try:
                template = PromptTemplate.from_file(prompt_file)
                self._templates[template.metadata.name] = template
            except Exception as e:
                # Skip invalid templates
                pass
    
    def list_prompts(self, category: Optional[PromptCategory] = None) -> List[str]:
        """List all available prompt templates.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            List of prompt names
        """
        if category is None:
            return list(self._templates.keys())
        
        return [
            name for name, template in self._templates.items()
            if template.metadata.category == category
        ]
    
    def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name.
        
        Args:
            name: Name of the prompt template
            
        Returns:
            Prompt template or None if not found
        """
        return self._templates.get(name)
    
    def render_prompt(self, name: str, variables: Dict[str, Any]) -> str:
        """Render a prompt template with variables.
        
        Args:
            name: Name of the prompt template
            variables: Variables to substitute
            
        Returns:
            Rendered prompt string
            
        Raises:
            KeyError: If prompt not found or required variable missing
        """
        template = self.get_prompt(name)
        if template is None:
            raise KeyError(f"Prompt template not found: {name}")
        
        return template.render(variables)
    
    def save_prompt(self, template: PromptTemplate) -> None:
        """Save a prompt template to disk.
        
        Args:
            template: Prompt template to save
        """
        prompts_dir = self.config.settings.prompts_dir
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        prompt_path = prompts_dir / f"{template.metadata.name}.json"
        template.save(prompt_path)
        
        self._templates[template.metadata.name] = template 