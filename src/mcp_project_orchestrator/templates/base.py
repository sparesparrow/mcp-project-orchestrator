"""
Base template class for the template system.

This module provides the base template class that defines common functionality
for all template types in the system.
"""

import os
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union

from .types import TemplateMetadata, TemplateFile

class BaseTemplate(ABC):
    """Base class for all templates.
    
    This abstract class defines the common interface and functionality that all
    template types must implement. It handles template metadata, file management,
    and variable substitution.
    
    Attributes:
        metadata (TemplateMetadata): Template metadata
        files (List[TemplateFile]): List of files in the template
        variables (Dict[str, str]): Template variables for substitution
    """
    
    def __init__(self, metadata: TemplateMetadata) -> None:
        """Initialize template with metadata.
        
        Args:
            metadata: Template metadata
        """
        self.metadata = metadata
        self.files: List[TemplateFile] = []
        self.variables: Dict[str, str] = metadata.variables.copy()
        
    def add_file(self, file: TemplateFile) -> None:
        """Add a file to the template.
        
        Args:
            file: Template file to add
        """
        self.files.append(file)
        
    def add_files(self, files: List[TemplateFile]) -> None:
        """Add multiple files to the template.
        
        Args:
            files: List of template files to add
        """
        self.files.extend(files)
        
    def set_variable(self, name: str, value: str) -> None:
        """Set a template variable.
        
        Args:
            name: Variable name
            value: Variable value
        """
        self.variables[name] = value
        
    def get_variable(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a template variable value.
        
        Args:
            name: Variable name
            default: Default value if variable not found
            
        Returns:
            Variable value or default if not found
        """
        return self.variables.get(name, default)
        
    def substitute_variables(self, content: str) -> str:
        """Substitute template variables in content.
        
        Args:
            content: Content containing variable placeholders
            
        Returns:
            Content with variables substituted
        """
        for name, value in self.variables.items():
            placeholder = f"{{{{ {name} }}}}"
            content = content.replace(placeholder, value)
        return content
        
    def save(self, path: Union[str, Path]) -> None:
        """Save template to disk.
        
        Args:
            path: Directory path to save template
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata_path = path / "template.json"
        with open(metadata_path, "w") as f:
            json.dump(self.metadata.to_dict(), f, indent=2)
            
        # Save files
        files_dir = path / "files"
        files_dir.mkdir(exist_ok=True)
        
        for file in self.files:
            file_path = files_dir / file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = self.substitute_variables(file.content)
            with open(file_path, "w") as f:
                f.write(content)
                
            if file.is_executable:
                os.chmod(file_path, 0o755)
                
    @classmethod
    def load(cls, path: Union[str, Path]) -> "BaseTemplate":
        """Load template from disk.
        
        Args:
            path: Directory path containing template
            
        Returns:
            Loaded template instance
            
        Raises:
            FileNotFoundError: If template files not found
            ValueError: If template metadata invalid
        """
        path = Path(path)
        
        # Load metadata
        metadata_path = path / "template.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Template metadata not found: {metadata_path}")
            
        with open(metadata_path) as f:
            metadata_dict = json.load(f)
            
        metadata = TemplateMetadata.from_dict(metadata_dict)
        template = cls(metadata)
        
        # Load files
        files_dir = path / "files"
        if not files_dir.exists():
            return template
            
        for file_path in files_dir.rglob("*"):
            if not file_path.is_file():
                continue
                
            relative_path = file_path.relative_to(files_dir)
            with open(file_path) as f:
                content = f.read()
                
            template_file = TemplateFile(
                path=str(relative_path),
                content=content,
                is_executable=os.access(file_path, os.X_OK)
            )
            template.add_file(template_file)
            
        return template
        
    @abstractmethod
    def validate(self) -> bool:
        """Validate template configuration.
        
        Returns:
            True if template is valid, False otherwise
        """
        pass
        
    @abstractmethod
    def apply(self, target_path: Union[str, Path]) -> None:
        """Apply template to target directory.
        
        Args:
            target_path: Directory path to apply template
            
        Raises:
            ValueError: If template validation fails
        """
        pass 