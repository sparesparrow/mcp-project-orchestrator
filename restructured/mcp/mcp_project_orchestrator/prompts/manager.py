"""Prompt manager for MCP Project Orchestrator.

This module provides the PromptManager class that handles prompt template
discovery, loading, and management.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..core.base import BaseManager
from ..core.config import Config
from ..core.exceptions import PromptError
from .template import PromptTemplate
from .category import PromptCategory
from .version import PromptVersion


class PromptManager(BaseManager):
    """Manager for prompt templates."""

    def __init__(self, config: Config):
        """Initialize prompt manager.

        Args:
            config: Configuration instance
        """
        super().__init__()
        self.config = config
        self.prompts: Dict[str, PromptTemplate] = {}
        self.categories: Dict[str, PromptCategory] = {}

    async def initialize(self) -> None:
        """Initialize the prompt manager.

        This method discovers and loads available prompts.
        """
        await self.discover_prompts()
        await self.load_categories()

    async def discover_prompts(self) -> None:
        """Discover and load available prompts."""
        prompts_dir = self.config.get_prompt_path()
        if not prompts_dir.exists():
            return

        for prompt_file in prompts_dir.rglob("*.json"):
            try:
                prompt = await self._load_prompt(prompt_file)
                self.prompts[prompt.name] = prompt
            except Exception as e:
                raise PromptError(
                    f"Failed to load prompt {prompt_file.name}",
                    str(prompt_file)
                ) from e

    async def load_categories(self) -> None:
        """Load prompt categories."""
        categories_file = self.config.get_prompt_path("categories.json")
        if not categories_file.exists():
            return

        try:
            with open(categories_file) as f:
                categories_data = json.load(f)

            for category_data in categories_data:
                category = PromptCategory(
                    name=category_data["name"],
                    description=category_data.get("description", ""),
                    prompts=category_data.get("prompts", [])
                )
                self.categories[category.name] = category
        except Exception as e:
            raise PromptError(
                "Failed to load prompt categories",
                str(categories_file)
            ) from e

    async def _load_prompt(self, prompt_file: Path) -> PromptTemplate:
        """Load a prompt template from a file.

        Args:
            prompt_file: Path to prompt file

        Returns:
            PromptTemplate: Loaded prompt template

        Raises:
            PromptError: If loading fails
        """
        try:
            with open(prompt_file) as f:
                data = json.load(f)

            version = PromptVersion(
                major=data.get("version", {}).get("major", 1),
                minor=data.get("version", {}).get("minor", 0),
                patch=data.get("version", {}).get("patch", 0)
            )

            return PromptTemplate(
                name=data.get("name", prompt_file.stem),
                description=data.get("description", ""),
                version=version,
                author=data.get("author", ""),
                template=data.get("template", ""),
                variables=data.get("variables", {}),
                category=data.get("category", "general"),
                tags=data.get("tags", [])
            )
        except Exception as e:
            raise PromptError(
                f"Failed to load prompt file {prompt_file}",
                str(prompt_file)
            ) from e

    async def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name.

        Args:
            name: Name of the prompt

        Returns:
            Optional[PromptTemplate]: The prompt if found, None otherwise
        """
        return self.prompts.get(name)

    async def get_category(self, name: str) -> Optional[PromptCategory]:
        """Get a prompt category by name.

        Args:
            name: Name of the category

        Returns:
            Optional[PromptCategory]: The category if found, None otherwise
        """
        return self.categories.get(name)

    async def list_prompts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available prompts.

        Args:
            category: Optional category to filter by

        Returns:
            List[Dict[str, Any]]: List of prompt metadata
        """
        prompts = self.prompts.values()
        if category:
            prompts = [p for p in prompts if p.category == category]

        return [
            {
                "name": prompt.name,
                "description": prompt.description,
                "version": str(prompt.version),
                "author": prompt.author,
                "category": prompt.category,
                "tags": prompt.tags,
            }
            for prompt in prompts
        ]

    async def list_categories(self) -> List[Dict[str, Any]]:
        """List all available categories.

        Returns:
            List[Dict[str, Any]]: List of category metadata
        """
        return [
            {
                "name": category.name,
                "description": category.description,
                "prompt_count": len(category.prompts),
            }
            for category in self.categories.values()
        ]

    async def render_prompt(
        self,
        name: str,
        variables: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """Render a prompt template with variables.

        Args:
            name: Name of the prompt
            variables: Template variables
            version: Optional specific version to use

        Returns:
            str: Rendered prompt

        Raises:
            PromptError: If prompt not found or rendering fails
        """
        prompt = await self.get_prompt(name)
        if not prompt:
            raise PromptError(f"Prompt not found: {name}")

        if version:
            if str(prompt.version) != version:
                raise PromptError(
                    f"Version mismatch: requested {version}, found {prompt.version}"
                )

        try:
            return await prompt.render(variables)
        except Exception as e:
            raise PromptError(
                f"Failed to render prompt {name}",
                name
            ) from e

    async def save_prompt(self, prompt: PromptTemplate) -> None:
        """Save a prompt template.

        Args:
            prompt: Prompt template to save

        Raises:
            PromptError: If saving fails
        """
        prompt_file = self.config.get_prompt_path(f"{prompt.name}.json")
        try:
            data = {
                "name": prompt.name,
                "description": prompt.description,
                "version": {
                    "major": prompt.version.major,
                    "minor": prompt.version.minor,
                    "patch": prompt.version.patch,
                },
                "author": prompt.author,
                "template": prompt.template,
                "variables": prompt.variables,
                "category": prompt.category,
                "tags": prompt.tags,
            }

            with open(prompt_file, "w") as f:
                json.dump(data, f, indent=2)

            self.prompts[prompt.name] = prompt
        except Exception as e:
            raise PromptError(
                f"Failed to save prompt {prompt.name}",
                str(prompt_file)
            ) from e 