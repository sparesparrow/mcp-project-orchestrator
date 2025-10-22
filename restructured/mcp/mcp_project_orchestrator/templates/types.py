"""
Type definitions for the template system.

This module defines enums and types used in the template system
for project and component templates.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

class TemplateType(Enum):
    """Types of templates supported."""
    
    PROJECT = "project"
    COMPONENT = "component"
    DOCUMENTATION = "documentation"
    WORKFLOW = "workflow"
    CONFIGURATION = "configuration"
    
    def __str__(self) -> str:
        return self.value

class TemplateCategory(Enum):
    """Categories for organizing templates."""
    
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    LIBRARY = "library"
    CLI = "cli"
    WEB_APP = "web_app"
    API = "api"
    DATABASE = "database"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"
    
    def __str__(self) -> str:
        return self.value

@dataclass
class TemplateMetadata:
    """Metadata for a template."""
    
    name: str
    description: str
    type: TemplateType
    category: Optional[TemplateCategory] = None
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Union[str, List[str], Dict[str, str]]]:
        """Convert metadata to dictionary format.
        
        Returns:
            Dictionary representation of the metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": str(self.type),
            "category": str(self.category) if self.category else None,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "variables": self.variables,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateMetadata":
        """Create metadata from dictionary.
        
        Args:
            data: Dictionary containing metadata fields
            
        Returns:
            TemplateMetadata instance
        """
        # Convert string values to enums
        if "type" in data:
            data["type"] = TemplateType(data["type"])
        if "category" in data and data["category"]:
            data["category"] = TemplateCategory(data["category"])
            
        return cls(**data)

@dataclass
class TemplateFile:
    """Represents a file in a template."""
    
    path: str
    content: str
    is_executable: bool = False
    variables: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Union[str, bool, Dict[str, str]]]:
        """Convert file data to dictionary format.
        
        Returns:
            Dictionary representation of the file data
        """
        return {
            "path": self.path,
            "content": self.content,
            "is_executable": self.is_executable,
            "variables": self.variables,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateFile":
        """Create file data from dictionary.
        
        Args:
            data: Dictionary containing file data fields
            
        Returns:
            TemplateFile instance
        """
        return cls(**data) 