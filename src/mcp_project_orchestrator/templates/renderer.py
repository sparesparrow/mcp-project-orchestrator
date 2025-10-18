"""Template renderer for MCP Project Orchestrator.

This module provides the TemplateRenderer class that handles template rendering
using Jinja2, with support for custom filters and extensions.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import re

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from ..core.exceptions import TemplateError


class TemplateRenderer:
    """Template renderer implementation."""

    def __init__(self, template_dir: Optional[Union[str, Path]] = None):
        """Initialize template renderer.

        Args:
            template_dir: Optional directory containing template files
        """
        self.template_dir = Path(template_dir) if template_dir else None
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)) if template_dir else None,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self._setup_filters()
        self._setup_extensions()

    def _setup_filters(self) -> None:
        """Set up custom Jinja2 filters."""
        self.env.filters.update({
            'camelcase': self._to_camel_case,
            'snakecase': self._to_snake_case,
            'kebabcase': self._to_kebab_case,
            'pascalcase': self._to_pascal_case,
            'quote': lambda s: f'"{s}"',
            'indent': self._indent_text,
        })

    def _setup_extensions(self) -> None:
        """Set up Jinja2 extensions."""
        self.env.add_extension('jinja2.ext.do')
        self.env.add_extension('jinja2.ext.loopcontrols')

    def render_string(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render a template string with context.

        Args:
            template_str: Template string to render
            context: Template variables

        Returns:
            str: Rendered content

        Raises:
            TemplateError: If rendering fails
        """
        try:
            template = Template(template_str, environment=self.env)
            return template.render(**context)
        except Exception as e:
            raise TemplateError(f"Failed to render template string: {str(e)}")

    def render_file(self, template_path: Union[str, Path], context: Dict[str, Any]) -> str:
        """Render a template file with context.

        Args:
            template_path: Path to template file
            context: Template variables

        Returns:
            str: Rendered content

        Raises:
            TemplateError: If rendering fails
        """
        if not self.template_dir:
            raise TemplateError("Template directory not set")

        try:
            template = self.env.get_template(str(template_path))
            return template.render(**context)
        except Exception as e:
            raise TemplateError(
                f"Failed to render template file {template_path}: {str(e)}"
            )

    @staticmethod
    def _to_camel_case(s: str) -> str:
        """Convert string to camelCase.

        Args:
            s: Input string

        Returns:
            str: Converted string
        """
        s = re.sub(r"[^a-zA-Z0-9]+", " ", s).title().replace(" ", "")
        return s[0].lower() + s[1:]

    @staticmethod
    def _to_snake_case(s: str) -> str:
        """Convert string to snake_case.

        Args:
            s: Input string

        Returns:
            str: Converted string
        """
        s = re.sub(r"[^a-zA-Z0-9]+", " ", s)
        return "_".join(s.lower().split())

    @staticmethod
    def _to_kebab_case(s: str) -> str:
        """Convert string to kebab-case.

        Args:
            s: Input string

        Returns:
            str: Converted string
        """
        s = re.sub(r"[^a-zA-Z0-9]+", " ", s)
        return "-".join(s.lower().split())

    @staticmethod
    def _to_pascal_case(s: str) -> str:
        """Convert string to PascalCase.

        Args:
            s: Input string

        Returns:
            str: Converted string
        """
        s = re.sub(r"[^a-zA-Z0-9]+", " ", s).title().replace(" ", "")
        return s

    @staticmethod
    def _indent_text(text: str, width: int = 4, first: bool = False) -> str:
        """Indent text by specified width.

        Args:
            text: Text to indent
            width: Number of spaces for indentation
            first: Whether to indent first line

        Returns:
            str: Indented text
        """
        prefix = " " * width
        lines = text.splitlines()
        if not lines:
            return ""
        if first:
            return "\n".join(prefix + line for line in lines)
        return "\n".join(
            prefix + line if line else line
            for line in lines
        ) 