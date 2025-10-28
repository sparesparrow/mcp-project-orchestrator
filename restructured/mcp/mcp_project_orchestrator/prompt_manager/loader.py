"""
Prompt loader for MCP Project Orchestrator.

This module provides functionality for loading prompt templates
from various sources (files, directories, remote repositories).
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set
import json
import aiohttp
import logging

from ..core import BaseOrchestrator, Config
from .template import PromptTemplate

class PromptLoader(BaseOrchestrator):
    """Class for loading prompt templates from various sources."""
    
    def __init__(self, config: Config):
        """Initialize the prompt loader.
        
        Args:
            config: Configuration instance
        """
        super().__init__(config)
        self.templates: Dict[str, PromptTemplate] = {}
        self.categories: Set[str] = set()
        self.tags: Set[str] = set()
        
    async def initialize(self) -> None:
        """Initialize the prompt loader.
        
        Loads templates from the configured templates directory.
        """
        await self.load_templates_from_directory(
            self.config.prompt_templates_dir
        )
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.templates.clear()
        self.categories.clear()
        self.tags.clear()
        
    async def load_templates_from_directory(
        self, directory: Path
    ) -> None:
        """Load all template files from a directory.
        
        Args:
            directory: Directory containing template files
            
        Raises:
            FileNotFoundError: If the directory doesn't exist
        """
        if not directory.exists():
            raise FileNotFoundError(f"Templates directory not found: {directory}")
            
        for file_path in directory.glob("*.json"):
            try:
                template = PromptTemplate.from_file(file_path)
                template.validate()
                self.templates[template.name] = template
                
                if template.category:
                    self.categories.add(template.category)
                self.tags.update(template.tags)
                
            except (json.JSONDecodeError, ValueError) as e:
                self.log_error(f"Error loading template {file_path}", e)
                
    async def load_template_from_url(self, url: str) -> Optional[PromptTemplate]:
        """Load a template from a URL.
        
        Args:
            url: URL of the template JSON file
            
        Returns:
            Loaded template or None if loading failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.log_error(
                            f"Failed to fetch template from {url}: "
                            f"Status {response.status}"
                        )
                        return None
                        
                    data = await response.json()
                    template = PromptTemplate(**data)
                    template.validate()
                    return template
                    
        except (aiohttp.ClientError, ValueError) as e:
            self.log_error(f"Error loading template from {url}", e)
            return None
            
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name.
        
        Args:
            name: Name of the template
            
        Returns:
            Template instance or None if not found
        """
        return self.templates.get(name)
        
    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """Get all templates in a category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of templates in the category
        """
        return [
            template for template in self.templates.values()
            if template.category == category
        ]
        
    def get_templates_by_tag(self, tag: str) -> List[PromptTemplate]:
        """Get all templates with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of templates with the tag
        """
        return [
            template for template in self.templates.values()
            if tag in template.tags
        ]
        
    def get_all_categories(self) -> List[str]:
        """Get all available categories.
        
        Returns:
            List of category names
        """
        return sorted(self.categories)
        
    def get_all_tags(self) -> List[str]:
        """Get all available tags.
        
        Returns:
            List of tag names
        """
        return sorted(self.tags) 