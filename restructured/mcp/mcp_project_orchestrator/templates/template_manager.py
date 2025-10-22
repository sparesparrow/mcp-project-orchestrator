#!/usr/bin/env python3
"""
Template Manager module for MCP Project Orchestrator.

This module manages the retrieval, selection, and application of project templates
and component templates. It loads templates from JSON files, allows selection 
based on design patterns, applies templates by creating the project structure, 
and generates basic documentation.
"""

import os
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class TemplateVersion:
    """Represents a template version with metadata."""
    major: int
    minor: int
    patch: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_string(cls, version_str: str) -> 'TemplateVersion':
        """Create a TemplateVersion from a string like '1.2.3'."""
        major, minor, patch = map(int, version_str.split('.'))
        now = datetime.now()
        return cls(major, minor, patch, now, now)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

class TemplateManager:
    """
    Manager for project and component templates.
    
    Attributes:
        templates_path: Optional path to the templates directory or file.
        project_templates: List of project templates loaded from JSON.
        component_templates: List of component templates loaded from JSON.
        template_versions: Dictionary mapping template names to their versions.
        template_inheritance: Dictionary tracking template inheritance relationships.
    """
    
    def __init__(self, templates_path: Optional[str] = None) -> None:
        """
        Initialize the TemplateManager.
        
        Args:
            templates_path: Optional path to templates. If not provided, defaults to
                            reading 'project_templates.json' and 'component_templates.json'
                            from the current working directory.
        """
        self.templates_path = templates_path
        self.template_versions: Dict[str, TemplateVersion] = {}
        self.template_inheritance: Dict[str, List[str]] = {}
        self.project_templates = self._load_templates("project_templates.json")
        self.component_templates = self._load_templates("component_templates.json")
    
    def _validate_template(self, template: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a template's structure and content.
        
        Args:
            template: The template dictionary to validate.
            
        Returns:
            A tuple of (is_valid, error_message).
        """
        required_fields = ["project_name", "version", "description", "components"]
        
        # Check required fields
        for field in required_fields:
            if field not in template:
                return False, f"Missing required field: {field}"
        
        # Validate version format
        version = template.get("version", "")
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            return False, "Invalid version format. Expected: X.Y.Z"
            
        # Validate components structure
        components = template.get("components", [])
        if not isinstance(components, list):
            return False, "Components must be a list"
            
        for comp in components:
            if not isinstance(comp, dict) or "name" not in comp:
                return False, "Each component must be a dictionary with at least a 'name' field"
                
        return True, ""

    def _load_templates(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load templates from the specified JSON file.
        
        Args:
            filename: The JSON file name to load templates from.
        
        Returns:
            A list of template dictionaries. If file not found or error occurs, returns an empty list.
        """
        paths_to_try = [
            self.templates_path if self.templates_path else filename,
            os.path.join(os.getcwd(), filename),
            os.path.join(os.getcwd(), "templates", filename),
            os.path.join(Path.home(), ".mcp", "templates", filename)
        ]
        
        for path in paths_to_try:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        templates = json.load(f)
                    if not isinstance(templates, list):
                        continue
                        
                    # Validate and process each template
                    valid_templates = []
                    for template in templates:
                        is_valid, error = self._validate_template(template)
                        if is_valid:
                            # Process version
                            name = template["project_name"]
                            version = template.get("version", "0.1.0")
                            self.template_versions[name] = TemplateVersion.from_string(version)
                            
                            # Process inheritance
                            if "extends" in template:
                                parent = template["extends"]
                                if parent not in self.template_inheritance:
                                    self.template_inheritance[parent] = []
                                self.template_inheritance[parent].append(name)
                                
                            valid_templates.append(template)
                            
                    return valid_templates
                except (json.JSONDecodeError, OSError):
                    continue
                    
        return []

    def get_template_version(self, template_name: str) -> Optional[TemplateVersion]:
        """
        Get the version information for a template.
        
        Args:
            template_name: Name of the template.
            
        Returns:
            TemplateVersion object if found, None otherwise.
        """
        return self.template_versions.get(template_name)

    def get_derived_templates(self, template_name: str) -> List[str]:
        """
        Get all templates that inherit from the specified template.
        
        Args:
            template_name: Name of the base template.
            
        Returns:
            List of template names that inherit from the specified template.
        """
        return self.template_inheritance.get(template_name, [])
    
    def get_project_templates(self) -> List[Dict[str, Any]]:
        """
        Retrieve project templates.
        
        Returns:
            A list of project templates.
        """
        return self.project_templates
    
    def get_component_templates(self) -> List[Dict[str, Any]]:
        """
        Retrieve component templates.
        
        Returns:
            A list of component templates.
        """
        return self.component_templates
    
    def _merge_templates(self, child: Dict[str, Any], parent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge a child template with its parent template.
        
        Args:
            child: The child template dictionary.
            parent: The parent template dictionary.
            
        Returns:
            A new dictionary containing the merged template.
        """
        merged = parent.copy()
        
        # Merge basic fields
        for field in ["project_name", "description", "version"]:
            if field in child:
                merged[field] = child[field]
                
        # Merge keywords
        merged["keywords"] = list(set(parent.get("keywords", []) + child.get("keywords", [])))
        
        # Merge components with override support
        parent_components = {comp["name"]: comp for comp in parent.get("components", [])}
        child_components = {comp["name"]: comp for comp in child.get("components", [])}
        
        # Start with parent components
        final_components = parent_components.copy()
        
        # Override or add child components
        final_components.update(child_components)
        
        merged["components"] = list(final_components.values())
        
        return merged

    def get_template_with_inheritance(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a template with all inherited properties merged.
        
        Args:
            template_name: Name of the template to retrieve.
            
        Returns:
            The merged template dictionary if found, None otherwise.
        """
        template = next((t for t in self.project_templates if t["project_name"] == template_name), None)
        if not template:
            return None
            
        # If template extends another, merge with parent
        if "extends" in template:
            parent_name = template["extends"]
            parent = self.get_template_with_inheritance(parent_name)  # Recursive call for nested inheritance
            if parent:
                template = self._merge_templates(template, parent)
                
        return template

    def reload_templates(self) -> None:
        """Reload all templates from disk."""
        self.template_versions.clear()
        self.template_inheritance.clear()
        self.project_templates = self._load_templates("project_templates.json")
        self.component_templates = self._load_templates("component_templates.json")

    def watch_templates(self, callback: Optional[callable] = None) -> None:
        """
        Start watching template files for changes.
        
        Args:
            callback: Optional function to call when templates are reloaded.
        """
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class TemplateHandler(FileSystemEventHandler):
            def __init__(self, manager: 'TemplateManager', callback: Optional[callable]):
                self.manager = manager
                self.callback = callback
                
            def on_modified(self, event):
                if event.src_path.endswith(('.json')):
                    self.manager.reload_templates()
                    if self.callback:
                        self.callback()
        
        paths_to_watch = [
            os.getcwd(),
            os.path.join(os.getcwd(), "templates"),
            os.path.join(Path.home(), ".mcp", "templates")
        ]
        
        observer = Observer()
        handler = TemplateHandler(self, callback)
        
        for path in paths_to_watch:
            if os.path.exists(path):
                observer.schedule(handler, path, recursive=False)
                
        observer.start()

    def select_template(self, description: str, patterns: List[str]) -> str:
        """
        Select an appropriate template based on the project description and design patterns.
        
        Args:
            description: Project description.
            patterns: List of identified design patterns.
        
        Returns:
            The name of the selected template. If no template matches, returns a default template name.
        """
        # Enhanced template selection logic
        best_match = None
        max_score = -1
        
        for template in self.project_templates:
            score = 0
            
            # Score based on keyword matches
            keywords = template.get("keywords", [])
            for pattern in patterns:
                if pattern in keywords:
                    score += 2
                    
            # Score based on description similarity
            template_desc = template.get("description", "").lower()
            description = description.lower()
            common_words = set(template_desc.split()) & set(description.split())
            score += len(common_words)
            
            # Check inheritance - templates that are more specialized (inherit from others) get a bonus
            if "extends" in template:
                score += 1
                
            if score > max_score:
                max_score = score
                best_match = template
                
        if best_match:
            return best_match.get("project_name", "DefaultProject")
            
        # Fallback to first template if available
        if self.project_templates:
            return self.project_templates[0].get("project_name", "DefaultProject")
            
        return "DefaultProject"
    
    def apply_template(self, template_name: str, project_name: str, description: str,
                       patterns: List[str], output_dir: str) -> Dict[str, Any]:
        """
        Apply the selected template: create the project directory structure and placeholder files.
        
        Args:
            template_name: Name of the template to use.
            project_name: Name of the new project.
            description: Description of the project.
            patterns: List of design patterns.
            output_dir: Directory where the project will be created.
        
        Returns:
            A dictionary containing the project path and a success message; otherwise, error details.
        """
        # Find the template by matching project_name
        template = next((t for t in self.project_templates if t.get("project_name") == template_name), None)
        if not template:
            return {"error": f"Template '{template_name}' not found."}
        
        project_path = os.path.join(output_dir, project_name)
        if os.path.exists(project_path):
            return {"error": f"Project '{project_name}' already exists."}
        
        try:
            # Create project structure directories
            os.makedirs(os.path.join(project_path, "src", "components"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "src", "interfaces"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "src", "services"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "src", "utils"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "tests"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "docs"), exist_ok=True)
            
            # Generate placeholder files for each component defined in the template
            components = template.get("components", [])
            for comp in components:
                comp_name = comp.get("name", "Component")
                # Create interface file
                interface_path = os.path.join(project_path, "src", "interfaces", f"i_{comp_name.lower()}.py")
                with open(interface_path, "w") as f:
                    f.write(f"# TODO: Define interface methods for {comp_name}\nclass I{comp_name}:\n    pass\n")
                # Create implementation file
                impl_path = os.path.join(project_path, "src", "components", f"{comp_name.lower()}.py")
                with open(impl_path, "w") as f:
                    f.write(f"# TODO: Implement {comp_name} logic\nclass {comp_name}:\n    pass\n")
                # Create service file (optional placeholder)
                service_path = os.path.join(project_path, "src", "services", f"{comp_name.lower()}_service.py")
                with open(service_path, "w") as f:
                    f.write(f"# TODO: Implement service logic for {comp_name}\n")
                # Create a basic README file
                readme_path = os.path.join(project_path, "README.md")
                with open(readme_path, "w") as f:
                    f.write(f"# {project_name}\n\n{description}\n")
            
            return {"project_path": project_path, "message": "Project created successfully."}
        except Exception as e:
            return {"error": str(e)}
    
    def generate_documentation(self, project_path: str) -> str:
        """
        Generate documentation for the project at the given path.
        
        Args:
            project_path: The path to the project directory.
        
        Returns:
            A string containing the generated documentation in Markdown format.
        """
        # Generate a placeholder README documentation
        doc = f"# Project Documentation\n\nProject path: {project_path}\n\n---\n\nThis documentation is auto-generated based on the project template."
        return doc
