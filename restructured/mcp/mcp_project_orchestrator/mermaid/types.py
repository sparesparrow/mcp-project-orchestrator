"""
Type definitions for Mermaid diagram generation.

This module defines enums and types used in Mermaid diagram
generation and rendering.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

class DiagramType(Enum):
    """Types of Mermaid diagrams supported."""
    
    FLOWCHART = "flowchart"
    SEQUENCE = "sequenceDiagram"
    CLASS = "classDiagram"
    STATE = "stateDiagram-v2"
    ENTITY_RELATIONSHIP = "erDiagram"
    GANTT = "gantt"
    PIE = "pie"
    MINDMAP = "mindmap"
    TIMELINE = "timeline"
    
    def __str__(self) -> str:
        return self.value

class RenderFormat(Enum):
    """Output formats for rendered diagrams."""
    
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    
    def __str__(self) -> str:
        return self.value

@dataclass
class DiagramConfig:
    """Configuration for a Mermaid diagram."""
    
    type: DiagramType
    title: Optional[str] = None
    theme: str = "default"
    background_color: str = "white"
    font_family: str = "arial"
    font_size: int = 14
    line_color: str = "black"
    line_width: int = 2
    
    def to_dict(self) -> Dict[str, Union[str, int]]:
        """Convert configuration to dictionary format.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "type": str(self.type),
            "title": self.title or "",
            "theme": self.theme,
            "backgroundColor": self.background_color,
            "fontFamily": self.font_family,
            "fontSize": self.font_size,
            "lineColor": self.line_color,
            "lineWidth": self.line_width,
        }

@dataclass
class RenderConfig:
    """Configuration for diagram rendering."""
    
    format: RenderFormat = RenderFormat.SVG
    width: int = 800
    height: int = 600
    scale: float = 1.0
    include_metadata: bool = True
    
    def to_dict(self) -> Dict[str, Union[str, int, float, bool]]:
        """Convert configuration to dictionary format.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "format": str(self.format),
            "width": self.width,
            "height": self.height,
            "scale": self.scale,
            "includeMetadata": self.include_metadata,
        } 


@dataclass
class DiagramMetadata:
    """Metadata for a diagram, used for save/load helpers in tests."""

    name: str
    description: str
    type: DiagramType
    version: str
    author: str
    tags: list[str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "type": str(self.type),
            "version": self.version,
            "author": self.author,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiagramMetadata":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            type=DiagramType(data["type"]),
            version=data.get("version", "0.1.0"),
            author=data.get("author", ""),
            tags=list(data.get("tags", [])),
        )