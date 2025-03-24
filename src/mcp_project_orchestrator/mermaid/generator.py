"""
Mermaid diagram generator for MCP Project Orchestrator.

This module provides functionality for generating Mermaid diagram
definitions from various inputs and templates.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

from ..core import BaseOrchestrator, Config
from .types import DiagramType, DiagramConfig

class MermaidGenerator(BaseOrchestrator):
    """Class for generating Mermaid diagram definitions."""
    
    def __init__(self, config: Config):
        """Initialize the Mermaid generator.
        
        Args:
            config: Configuration instance
        """
        super().__init__(config)
        self.templates_dir = self.config.templates_dir / "mermaid"
        self.templates: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """Initialize the generator.
        
        Creates the templates directory if it doesn't exist and
        loads any existing templates.
        """
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        await self.load_templates()
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.templates.clear()
        
    async def load_templates(self) -> None:
        """Load Mermaid diagram templates from the templates directory."""
        for file_path in self.templates_dir.glob("*.json"):
            try:
                template = self.load_json(file_path)
                self.templates[file_path.stem] = template
            except Exception as e:
                self.log_error(f"Error loading template {file_path}", e)
                
    def generate_flowchart(
        self,
        nodes: List[Dict[str, str]],
        edges: List[Dict[str, str]],
        direction: str = "TB",
        config: Optional[DiagramConfig] = None,
    ) -> str:
        """Generate a flowchart diagram definition.
        
        Args:
            nodes: List of node definitions
            edges: List of edge definitions
            direction: Flow direction (TB, BT, LR, RL)
            config: Optional diagram configuration
            
        Returns:
            Mermaid flowchart definition
        """
        if config is None:
            config = DiagramConfig(type=DiagramType.FLOWCHART)
            
        lines = [f"flowchart {direction}"]
        
        # Add nodes
        for node in nodes:
            node_id = node["id"]
            node_label = node.get("label", node_id)
            node_shape = node.get("shape", "")
            
            if node_shape:
                lines.append(f"    {node_id}[{node_label}]{{{node_shape}}}")
            else:
                lines.append(f"    {node_id}[{node_label}]")
                
        # Add edges
        for edge in edges:
            from_node = edge["from"]
            to_node = edge["to"]
            edge_label = edge.get("label", "")
            edge_style = edge.get("style", "-->")
            
            if edge_label:
                lines.append(f"    {from_node} {edge_style}|{edge_label}| {to_node}")
            else:
                lines.append(f"    {from_node} {edge_style} {to_node}")
                
        return "\n".join(lines)
        
    def generate_class_diagram(
        self,
        classes: List[Dict[str, Any]],
        relationships: List[Dict[str, str]],
        config: Optional[DiagramConfig] = None,
    ) -> str:
        """Generate a class diagram definition.
        
        Args:
            classes: List of class definitions
            relationships: List of class relationships
            config: Optional diagram configuration
            
        Returns:
            Mermaid class diagram definition
        """
        if config is None:
            config = DiagramConfig(type=DiagramType.CLASS)
            
        lines = ["classDiagram"]
        
        # Add classes
        for class_def in classes:
            class_name = class_def["name"]
            
            # Class definition
            lines.append(f"    class {class_name} {{")
            
            # Properties
            for prop in class_def.get("properties", []):
                prop_name = prop["name"]
                prop_type = prop.get("type", "")
                prop_visibility = prop.get("visibility", "+")
                
                if prop_type:
                    lines.append(f"        {prop_visibility}{prop_name}: {prop_type}")
                else:
                    lines.append(f"        {prop_visibility}{prop_name}")
                    
            # Methods
            for method in class_def.get("methods", []):
                method_name = method["name"]
                method_params = method.get("params", "")
                method_return = method.get("return", "")
                method_visibility = method.get("visibility", "+")
                
                if method_return:
                    lines.append(
                        f"        {method_visibility}{method_name}({method_params}) {method_return}"
                    )
                else:
                    lines.append(f"        {method_visibility}{method_name}({method_params})")
                    
            lines.append("    }")
            
        # Add relationships
        for rel in relationships:
            from_class = rel["from"]
            to_class = rel["to"]
            rel_type = rel.get("type", "--")
            rel_label = rel.get("label", "")
            
            if rel_label:
                lines.append(f"    {from_class} {rel_type} {to_class}: {rel_label}")
            else:
                lines.append(f"    {from_class} {rel_type} {to_class}")
                
        return "\n".join(lines)
        
    def generate_sequence_diagram(
        self,
        participants: List[Dict[str, str]],
        messages: List[Dict[str, str]],
        config: Optional[DiagramConfig] = None,
    ) -> str:
        """Generate a sequence diagram definition.
        
        Args:
            participants: List of participant definitions
            messages: List of message definitions
            config: Optional diagram configuration
            
        Returns:
            Mermaid sequence diagram definition
        """
        if config is None:
            config = DiagramConfig(type=DiagramType.SEQUENCE)
            
        lines = ["sequenceDiagram"]
        
        # Add participants
        for participant in participants:
            participant_id = participant["id"]
            participant_label = participant.get("label", participant_id)
            lines.append(f"    participant {participant_id} as {participant_label}")
            
        # Add messages
        for message in messages:
            from_participant = message["from"]
            to_participant = message["to"]
            message_text = message["text"]
            message_type = message.get("type", "->")
            
            lines.append(f"    {from_participant}{message_type}{to_participant}: {message_text}")
            
            # Add optional activation/deactivation
            if message.get("activate", False):
                lines.append(f"    activate {to_participant}")
            if message.get("deactivate", False):
                lines.append(f"    deactivate {to_participant}")
                
        return "\n".join(lines)
        
    def generate_from_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        config: Optional[DiagramConfig] = None,
    ) -> Optional[str]:
        """Generate a diagram definition from a template.
        
        Args:
            template_name: Name of the template to use
            variables: Variables to substitute in the template
            config: Optional diagram configuration
            
        Returns:
            Generated diagram definition or None if template not found
        """
        template = self.templates.get(template_name)
        if not template:
            return None
            
        try:
            # Get the template content and diagram type
            content = template["content"]
            diagram_type = template.get("type", "flowchart")
            
            # Replace variables in the template
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                content = content.replace(placeholder, str(var_value))
                
            # Add configuration if provided
            if config:
                config_dict = config.to_dict()
                for key, value in config_dict.items():
                    if key in template.get("config", {}):
                        content = content.replace(f"{{{key}}}", str(value))
                        
            return content
            
        except Exception as e:
            self.log_error(f"Error generating diagram from template {template_name}", e)
            return None
            
    def save_template(
        self,
        name: str,
        content: str,
        diagram_type: DiagramType,
        variables: Optional[Dict[str, str]] = None,
    ) -> None:
        """Save a new diagram template.
        
        Args:
            name: Template name
            content: Template content
            diagram_type: Type of diagram
            variables: Optional dictionary of variable descriptions
        """
        template = {
            "name": name,
            "type": str(diagram_type),
            "content": content,
            "variables": variables or {},
        }
        
        file_path = self.templates_dir / f"{name}.json"
        self.save_json(file_path, template)
        self.templates[name] = template 