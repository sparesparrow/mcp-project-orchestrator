"""
Project and component templates for the MCP Project Orchestrator.

This package exposes a simple template API used in tests:
- TemplateType, TemplateCategory, TemplateMetadata, TemplateFile
- ProjectTemplate, ComponentTemplate
- TemplateManager (directory-based discovery)
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

from .types import TemplateType, TemplateCategory, TemplateMetadata, TemplateFile
from .base import BaseTemplate


class ProjectTemplate(BaseTemplate):
    """Project template with validation and apply logic for tests."""

    def validate(self) -> bool:
        # Valid if at least one file is present
        return len(self.files) > 0

    def apply(self, target_path: Union[str, Path]) -> None:
        target_path = Path(target_path)
        target_path.mkdir(parents=True, exist_ok=True)

        # Create a nested directory named after the project if provided
        project_dir_name = self.get_variable("project_name", "Project")
        project_root = target_path / project_dir_name
        project_root.mkdir(parents=True, exist_ok=True)

        for file in self.files:
            dest = project_root / file.path
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = self.substitute_variables_jinja2(file.content) if file.path.endswith(".jinja2") else self.substitute_variables(file.content)
            dest.write_text(content)


class ComponentTemplate(BaseTemplate):
    """Component template with validation and apply logic for tests."""

    def validate(self) -> bool:
        # Valid if at least one file is present
        return len(self.files) > 0

    def apply(self, target_path: Union[str, Path]) -> None:
        target_path = Path(target_path)
        target_path.mkdir(parents=True, exist_ok=True)

        for file in self.files:
            # Substitute variables in the file path as well
            file_path = self.substitute_variables(file.path)
            dest = target_path / file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = self.substitute_variables_jinja2(file.content) if file.path.endswith(".jinja2") else self.substitute_variables(file.content)
            dest.write_text(content)


class TemplateManager:
    """Directory-based template discovery and access used in tests."""

    def __init__(self, templates_dir: Union[str, Path, None] = None) -> None:
        self.templates_dir = Path(templates_dir) if templates_dir else Path.cwd() / "templates"
        self._templates: Dict[str, BaseTemplate] = {}

    def discover_templates(self) -> None:
        self._templates.clear()
        if not self.templates_dir.exists():
            return
        for sub in self.templates_dir.iterdir():
            if not sub.is_dir():
                continue
            metadata_path = sub / "template.json"
            if not metadata_path.exists():
                continue
            try:
                meta = TemplateMetadata.from_dict(__import__("json").load(open(metadata_path)))
            except Exception:
                continue
            # Choose template class based on type
            if meta.type == TemplateType.PROJECT:
                template = ProjectTemplate(meta)
            else:
                template = ComponentTemplate(meta)

            # Load files directory if present
            files_dir = sub / "files"
            if files_dir.exists():
                for fp in files_dir.rglob("*"):
                    if fp.is_file():
                        rel = fp.relative_to(files_dir)
                        content = fp.read_text()
                        template.add_file(TemplateFile(path=str(rel), content=content))

            self._templates[meta.name] = template

    def list_templates(self, template_type: Optional[TemplateType] = None) -> List[str]:
        if template_type is None:
            return list(self._templates.keys())
        return [name for name, t in self._templates.items() if isinstance(t, ProjectTemplate) and template_type == TemplateType.PROJECT or isinstance(t, ComponentTemplate) and template_type == TemplateType.COMPONENT]

    def get_template(self, name: str) -> Optional[BaseTemplate]:
        return self._templates.get(name)


__all__ = [
    "TemplateType",
    "TemplateCategory",
    "TemplateMetadata",
    "TemplateFile",
    "ProjectTemplate",
    "ComponentTemplate",
    "TemplateManager",
]

    def apply_template(self, template_name: str, variables: dict, target_dir: str) -> None:
        """Apply a template with variables to create a new project"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Set variables
        for key, value in variables.items():
            template.set_variable(key, str(value))
        
        # Apply template
        template.apply(target_dir)
