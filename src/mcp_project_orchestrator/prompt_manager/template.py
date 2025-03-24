"""
Prompt template class for MCP Project Orchestrator.

This module defines the PromptTemplate class that represents a single
prompt template with its metadata and rendering capabilities.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

@dataclass
class PromptTemplate:
    """Class representing a prompt template."""
    
    name: str
    content: str
    description: str
    variables: Dict[str, str] = field(default_factory=dict)
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: Optional[str] = None
    examples: List[Dict[str, str]] = field(default_factory=list)
    
    @classmethod
    def from_file(cls, path: Path) -> "PromptTemplate":
        """Load a prompt template from a JSON file.
        
        Args:
            path: Path to the JSON template file
            
        Returns:
            Loaded PromptTemplate instance
            
        Raises:
            FileNotFoundError: If the template file doesn't exist
            ValueError: If the template is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")
            
        with open(path) as f:
            data = json.load(f)
            
        required_fields = {"name", "content", "description"}
        missing_fields = required_fields - set(data.keys())
        
        if missing_fields:
            raise ValueError(
                f"Template is missing required fields: {missing_fields}"
            )
            
        return cls(**data)
        
    def render(self, variables: Dict[str, Any]) -> str:
        """Render the template with the provided variables.
        
        Args:
            variables: Dictionary of variables to substitute in the template
            
        Returns:
            Rendered prompt string
            
        Raises:
            KeyError: If a required variable is missing
        """
        result = self.content
        
        for var_name, var_desc in self.variables.items():
            if var_name not in variables:
                raise KeyError(
                    f"Missing required variable '{var_name}': {var_desc}"
                )
            placeholder = f"{{{var_name}}}"
            result = result.replace(placeholder, str(variables[var_name]))
            
        return result
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary.
        
        Returns:
            Dictionary representation of the template
        """
        return {
            "name": self.name,
            "content": self.content,
            "description": self.description,
            "variables": self.variables,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "author": self.author,
            "examples": self.examples,
        }
        
    def save(self, path: Path) -> None:
        """Save the template to a JSON file.
        
        Args:
            path: Path where to save the template
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
            
    def validate(self) -> None:
        """Validate the template.
        
        Raises:
            ValueError: If the template is invalid
        """
        if not self.name:
            raise ValueError("Template name cannot be empty")
            
        if not self.content:
            raise ValueError("Template content cannot be empty")
            
        if not self.description:
            raise ValueError("Template description cannot be empty")
            
        # Validate that all variables in content have descriptions
        content_vars = {
            name.strip("{}") for name in 
            (var for var in self.content.split("{") if "}" in var)
        }
        
        missing_vars = content_vars - set(self.variables.keys())
        if missing_vars:
            raise ValueError(
                f"Template uses variables without descriptions: {missing_vars}"
            ) 