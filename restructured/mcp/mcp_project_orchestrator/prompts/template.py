"""Prompt template implementation for MCP Project Orchestrator.

This module provides the PromptTemplate class that handles individual prompt
templates, including loading, validation, and rendering.
"""

from typing import Dict, List, Any, Optional
from jinja2 import Environment, Template, StrictUndefined

from ..core.exceptions import PromptError
from .version import PromptVersion


class PromptTemplate:
    """Class representing a prompt template."""

    def __init__(
        self,
        name: str,
        description: str,
        version: PromptVersion,
        author: str,
        template: str,
        variables: Dict[str, Any],
        category: str = "general",
        tags: Optional[List[str]] = None
    ):
        """Initialize prompt template.

        Args:
            name: Template name
            description: Template description
            version: Template version
            author: Template author
            template: Template content
            variables: Template variables with descriptions
            category: Template category
            tags: Template tags
        """
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.template = template
        self.variables = variables
        self.category = category
        self.tags = tags or []

        self._jinja_env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        self._compiled_template: Optional[Template] = None

    async def validate(self) -> None:
        """Validate the prompt template.

        This method checks that:
        - Required fields are present
        - Template syntax is valid
        - Variable references are valid

        Raises:
            PromptError: If validation fails
        """
        if not self.name:
            raise PromptError("Template name is required")

        if not self.template:
            raise PromptError("Template content is required")

        try:
            self._compiled_template = self._jinja_env.from_string(self.template)
        except Exception as e:
            raise PromptError(
                f"Invalid template syntax in {self.name}",
                self.name
            ) from e

        # Validate variable references
        try:
            # Create dummy variables with None values
            dummy_vars = {name: None for name in self.variables}
            self._compiled_template.render(**dummy_vars)
        except Exception as e:
            raise PromptError(
                f"Invalid variable references in {self.name}",
                self.name
            ) from e

    async def render(self, variables: Dict[str, Any]) -> str:
        """Render the prompt template with variables.

        Args:
            variables: Template variables

        Returns:
            str: Rendered prompt

        Raises:
            PromptError: If rendering fails
        """
        if not self._compiled_template:
            await self.validate()

        try:
            # Validate required variables are provided
            missing = set(self.variables) - set(variables)
            if missing:
                raise PromptError(
                    f"Missing required variables: {', '.join(missing)}",
                    self.name
                )

            return self._compiled_template.render(**variables)
        except Exception as e:
            raise PromptError(
                f"Failed to render template {self.name}",
                self.name
            ) from e

    def get_variable_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about template variables.

        Returns:
            Dict[str, Dict[str, Any]]: Variable information
        """
        return self.variables

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": {
                "major": self.version.major,
                "minor": self.version.minor,
                "patch": self.version.patch,
            },
            "author": self.author,
            "template": self.template,
            "variables": self.variables,
            "category": self.category,
            "tags": self.tags,
        }

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            str: String representation
        """
        return f"{self.name} (v{self.version})"

    def __repr__(self) -> str:
        """Get detailed string representation.

        Returns:
            str: Detailed string representation
        """
        return (
            f"PromptTemplate(name='{self.name}', "
            f"version={self.version}, "
            f"category='{self.category}')"
        ) 