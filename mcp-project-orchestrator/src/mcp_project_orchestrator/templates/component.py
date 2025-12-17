"""Component template implementation for MCP Project Orchestrator.

This module provides the ComponentTemplate class that handles component template
loading, validation, and application.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from jinja2 import Environment, FileSystemLoader, Template

from ..core.base import BaseTemplate
from ..core.exceptions import TemplateError


class ComponentTemplate(BaseTemplate):
    """Component template implementation."""

    def __init__(
        self,
        name: str,
        description: str,
        version: str,
        author: str,
        template_dir: Path,
        variables: Dict[str, Any],
        files: List[Dict[str, Any]],
        dependencies: List[str]
    ):
        """Initialize component template.

        Args:
            name: Template name
            description: Template description
            version: Template version
            author: Template author
            template_dir: Directory containing template files
            variables: Template variables schema
            files: List of template files
            dependencies: List of component dependencies
        """
        super().__init__(template_dir)
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.variables = variables
        self.files = files
        self.dependencies = dependencies
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def validate(self) -> bool:
        """Validate template structure and content.

        Returns:
            bool: True if valid, False otherwise

        Raises:
            TemplateError: If validation fails
        """
        # Check template directory exists
        if not self.template_path.exists():
            raise TemplateError(
                f"Template directory not found: {self.template_path}",
                str(self.template_path)
            )

        # Validate required files exist
        required_files = ["template.json"]
        for file in required_files:
            if not (self.template_path / file).exists():
                raise TemplateError(
                    f"Required file not found: {file}",
                    str(self.template_path / file)
                )

        # Validate template files exist
        for file_info in self.files:
            file_path = self.template_path / file_info["source"]
            if not file_path.exists():
                raise TemplateError(
                    f"Template file not found: {file_info['source']}",
                    str(file_path)
                )

        return True

    async def render(self, context: Dict[str, Any]) -> str:
        """Render template content with context.

        Args:
            context: Template variables

        Returns:
            str: Rendered content

        Raises:
            TemplateError: If rendering fails
        """
        try:
            template = self.env.get_template(str(self.template_path))
            return template.render(**context)
        except Exception as e:
            raise TemplateError(
                f"Failed to render template: {str(e)}",
                str(self.template_path)
            ) from e

    async def apply(self, target_dir: Path, variables: Dict[str, Any]) -> None:
        """Apply template to target directory.

        Args:
            target_dir: Target directory for component
            variables: Template variables

        Raises:
            TemplateError: If template application fails
        """
        # Validate template first
        await self.validate()

        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)

        # Process each template file
        for file_info in self.files:
            source = self.template_path / file_info["source"]
            target = target_dir / file_info["target"]

            # Create parent directories
            target.parent.mkdir(parents=True, exist_ok=True)

            if file_info.get("template", True):
                # Render template file
                try:
                    template = Template(source.read_text())
                    rendered = template.render(**variables)
                    target.write_text(rendered)
                except Exception as e:
                    raise TemplateError(
                        f"Failed to render template file {source}: {str(e)}",
                        str(source)
                    ) from e
            else:
                # Copy file as-is
                shutil.copy2(source, target)

    async def get_dependencies(self) -> List[str]:
        """Get list of component dependencies.

        Returns:
            List[str]: List of dependency names
        """
        return self.dependencies.copy()

    async def validate_dependencies(self, available_components: List[str]) -> bool:
        """Validate that all dependencies are available.

        Args:
            available_components: List of available component names

        Returns:
            bool: True if all dependencies are available

        Raises:
            TemplateError: If dependencies are missing
        """
        missing = set(self.dependencies) - set(available_components)
        if missing:
            raise TemplateError(
                f"Missing dependencies: {', '.join(missing)}",
                str(self.template_path)
            )
        return True 