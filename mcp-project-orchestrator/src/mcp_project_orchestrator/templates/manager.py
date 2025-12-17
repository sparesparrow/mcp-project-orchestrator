"""Template manager for MCP Project Orchestrator.

This module provides the TemplateManager class that handles template discovery,
loading, and management of project and component templates.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..core.base import BaseManager, BaseComponent
from ..core.config import Config
from ..core.exceptions import TemplateError
from .project import ProjectTemplate
from .component import ComponentTemplate


class TemplateManager(BaseManager):
    """Manager for project and component templates."""

    def __init__(self, config: Config):
        """Initialize the template manager.

        Args:
            config: Configuration instance
        """
        super().__init__()
        self.config = config
        self.project_templates: Dict[str, ProjectTemplate] = {}
        self.component_templates: Dict[str, ComponentTemplate] = {}

    async def initialize(self) -> None:
        """Initialize the template manager.

        This method discovers and loads available templates.
        """
        await self.discover_templates()

    async def discover_templates(self) -> None:
        """Discover and load available templates."""
        # Discover project templates
        project_templates_dir = self.config.get_template_path("projects")
        if project_templates_dir.exists():
            for template_dir in project_templates_dir.iterdir():
                if template_dir.is_dir():
                    try:
                        template = await self._load_project_template(template_dir)
                        self.project_templates[template.name] = template
                    except Exception as e:
                        raise TemplateError(
                            f"Failed to load project template {template_dir.name}",
                            str(template_dir)
                        ) from e

        # Discover component templates
        component_templates_dir = self.config.get_template_path("components")
        if component_templates_dir.exists():
            for template_dir in component_templates_dir.iterdir():
                if template_dir.is_dir():
                    try:
                        template = await self._load_component_template(template_dir)
                        self.component_templates[template.name] = template
                    except Exception as e:
                        raise TemplateError(
                            f"Failed to load component template {template_dir.name}",
                            str(template_dir)
                        ) from e

    async def _load_project_template(self, template_dir: Path) -> ProjectTemplate:
        """Load a project template from a directory.

        Args:
            template_dir: Directory containing the template

        Returns:
            ProjectTemplate: Loaded project template
        """
        metadata_file = template_dir / "template.json"
        if not metadata_file.exists():
            raise TemplateError(
                f"Template metadata file not found: {metadata_file}",
                str(template_dir)
            )

        with open(metadata_file) as f:
            metadata = json.load(f)

        return ProjectTemplate(
            name=metadata.get("name", template_dir.name),
            description=metadata.get("description", ""),
            version=metadata.get("version", "0.1.0"),
            author=metadata.get("author", ""),
            template_dir=template_dir,
            variables=metadata.get("variables", {}),
            files=metadata.get("files", []),
            hooks=metadata.get("hooks", {})
        )

    async def _load_component_template(self, template_dir: Path) -> ComponentTemplate:
        """Load a component template from a directory.

        Args:
            template_dir: Directory containing the template

        Returns:
            ComponentTemplate: Loaded component template
        """
        metadata_file = template_dir / "template.json"
        if not metadata_file.exists():
            raise TemplateError(
                f"Template metadata file not found: {metadata_file}",
                str(template_dir)
            )

        with open(metadata_file) as f:
            metadata = json.load(f)

        return ComponentTemplate(
            name=metadata.get("name", template_dir.name),
            description=metadata.get("description", ""),
            version=metadata.get("version", "0.1.0"),
            author=metadata.get("author", ""),
            template_dir=template_dir,
            variables=metadata.get("variables", {}),
            files=metadata.get("files", []),
            dependencies=metadata.get("dependencies", [])
        )

    async def get_project_template(self, name: str) -> Optional[ProjectTemplate]:
        """Get a project template by name.

        Args:
            name: Name of the template

        Returns:
            Optional[ProjectTemplate]: The template if found, None otherwise
        """
        return self.project_templates.get(name)

    async def get_component_template(self, name: str) -> Optional[ComponentTemplate]:
        """Get a component template by name.

        Args:
            name: Name of the template

        Returns:
            Optional[ComponentTemplate]: The template if found, None otherwise
        """
        return self.component_templates.get(name)

    async def list_project_templates(self) -> List[Dict[str, Any]]:
        """List all available project templates.

        Returns:
            List[Dict[str, Any]]: List of template metadata
        """
        return [
            {
                "name": template.name,
                "description": template.description,
                "version": template.version,
                "author": template.author,
            }
            for template in self.project_templates.values()
        ]

    async def list_component_templates(self) -> List[Dict[str, Any]]:
        """List all available component templates.

        Returns:
            List[Dict[str, Any]]: List of template metadata
        """
        return [
            {
                "name": template.name,
                "description": template.description,
                "version": template.version,
                "author": template.author,
            }
            for template in self.component_templates.values()
        ]

    async def apply_project_template(
        self,
        template_name: str,
        target_dir: Union[str, Path],
        variables: Dict[str, Any]
    ) -> None:
        """Apply a project template to a target directory.

        Args:
            template_name: Name of the template to apply
            target_dir: Target directory for the project
            variables: Template variables
        """
        template = await self.get_project_template(template_name)
        if not template:
            raise TemplateError(f"Project template not found: {template_name}")

        await template.apply(Path(target_dir), variables)

    async def apply_component_template(
        self,
        template_name: str,
        target_dir: Union[str, Path],
        variables: Dict[str, Any]
    ) -> None:
        """Apply a component template to a target directory.

        Args:
            template_name: Name of the template to apply
            target_dir: Target directory for the component
            variables: Template variables
        """
        template = await self.get_component_template(template_name)
        if not template:
            raise TemplateError(f"Component template not found: {template_name}")

        await template.apply(Path(target_dir), variables) 