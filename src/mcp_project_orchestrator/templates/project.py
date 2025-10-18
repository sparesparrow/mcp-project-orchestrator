"""Project template implementation for MCP Project Orchestrator.

This module provides the ProjectTemplate class that handles project template
loading, validation, and application.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import json
import subprocess

from jinja2 import Environment, FileSystemLoader, Template

from ..core.base import BaseTemplate
from ..core.exceptions import TemplateError


class ProjectTemplate(BaseTemplate):
    """Project template implementation."""

    def __init__(
        self,
        name: str,
        description: str,
        version: str,
        author: str,
        template_dir: Path,
        variables: Dict[str, Any],
        files: List[Dict[str, Any]],
        hooks: Dict[str, Any]
    ):
        """Initialize project template.

        Args:
            name: Template name
            description: Template description
            version: Template version
            author: Template author
            template_dir: Directory containing template files
            variables: Template variables schema
            files: List of template files
            hooks: Template hooks configuration
        """
        super().__init__(template_dir)
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.variables = variables
        self.files = files
        self.hooks = hooks
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
            target_dir: Target directory for project
            variables: Template variables

        Raises:
            TemplateError: If template application fails
        """
        # Validate template first
        await self.validate()

        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)

        # Run pre-apply hooks
        await self._run_hooks("pre_apply", variables)

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

        # Run post-apply hooks
        await self._run_hooks("post_apply", variables)

    async def _run_hooks(self, hook_type: str, variables: Dict[str, Any]) -> None:
        """Run template hooks.

        Args:
            hook_type: Type of hook to run (pre_apply or post_apply)
            variables: Template variables

        Raises:
            TemplateError: If hook execution fails
        """
        hooks = self.hooks.get(hook_type, [])
        for hook in hooks:
            if hook["type"] == "command":
                try:
                    subprocess.run(
                        hook["command"],
                        shell=True,
                        check=True,
                        cwd=str(self.template_path)
                    )
                except subprocess.CalledProcessError as e:
                    raise TemplateError(
                        f"Hook command failed: {hook['command']}",
                        str(self.template_path)
                    ) from e
            elif hook["type"] == "python":
                try:
                    hook_func: Callable = eval(hook["code"])  # nosec
                    hook_func(variables)
                except Exception as e:
                    raise TemplateError(
                        f"Python hook failed: {str(e)}",
                        str(self.template_path)
                    ) from e 