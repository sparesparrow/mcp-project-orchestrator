"""
Mermaid diagram generator for MCP Project Orchestrator.

This module provides functionality for generating Mermaid diagram
definitions from various inputs and templates.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

from ..core import Config
from .types import DiagramType, DiagramConfig, DiagramMetadata

class MermaidGenerator:
    """Class for generating Mermaid diagram definitions."""
    
    def __init__(self, config: Config):
        """Initialize the Mermaid generator.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        templates_base = getattr(config.settings, 'templates_dir', Path('templates'))
        self.templates_dir = templates_base / "mermaid"
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
                with open(file_path) as f:
                    template = json.load(f)
                self.templates[file_path.stem] = template
            except Exception as e:
                pass  # Skip invalid templates
                
    def generate_flowchart(
        self,
        nodes: List[Dict[str, str]] | List[tuple],
        edges: List[Dict[str, str]] | List[tuple],
        direction: str = "TD",
        config: Optional[DiagramConfig] = None,
    ) -> str:
        """Generate a flowchart diagram definition.
        
        Args:
            nodes: List of node definitions
            edges: List of edge definitions
            direction: Flow direction (TD, BT, LR, RL) - TD by default
            config: Optional diagram configuration
            
        Returns:
            Mermaid flowchart definition
        """
        if config is None:
            config = DiagramConfig(type=DiagramType.FLOWCHART)
            
        lines = [f"flowchart {direction}"]
        
        # Add nodes
        for node in nodes:
            if isinstance(node, dict):
                node_id = node["id"]
                node_label = node.get("label", node_id)
            else:
                node_id, node_label = node[0], node[1]
            node_shape = ""
            
            if node_shape:
                lines.append(f"    {node_id}[{node_label}]{{{node_shape}}}")
            else:
                lines.append(f"    {node_id}[{node_label}]")
                
        # Add edges
        for edge in edges:
            if isinstance(edge, dict):
                from_node = edge["from"]
                to_node = edge["to"]
                edge_label = edge.get("label", "")
                edge_style = edge.get("style", "-->")
            else:
                from_node, to_node, edge_label = edge
                edge_style = "-->"
            
            if edge_label:
                lines.append(f"    {from_node} {edge_style}|{edge_label}| {to_node}")
            else:
                lines.append(f"    {from_node} {edge_style} {to_node}")
                
        return "\n".join(lines)
        
    def generate_class(
        self,
        classes: List[Dict[str, Any]],
        relationships: List[tuple],
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
            for prop in class_def.get("attributes", []) or class_def.get("properties", []):
                if isinstance(prop, str):
                    lines.append(f"        +{prop}")
                    continue
                prop_name = prop.get("name", prop)
                prop_type = prop.get("type", "")
                prop_visibility = prop.get("visibility", "+")
                
                if prop_type:
                    lines.append(f"        {prop_visibility}{prop_name}: {prop_type}")
                else:
                    lines.append(f"        {prop_visibility}{prop_name}")
                    
            # Methods
            for method in class_def.get("methods", []):
                if isinstance(method, str):
                    lines.append(f"        +{method}")
                    continue
                method_name = method.get("name", method)
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
            if isinstance(rel, tuple):
                from_class, to_class, rel_type = rel
                # Map relationship type to Mermaid syntax
                rel_symbol = "--"
                if rel_type == "extends":
                    rel_symbol = "--|>"
                elif rel_type == "implements":
                    rel_symbol = "..|>"
                elif rel_type == "composition":
                    rel_symbol = "*--"
                elif rel_type == "aggregation":
                    rel_symbol = "o--"
                lines.append(f"    {from_class} {rel_symbol} {to_class}")
            else:
                from_class = rel["from"]
                to_class = rel["to"]
                rel_type = rel.get("type", "--")
                rel_label = rel.get("label", "")
                
                if rel_label:
                    lines.append(f"    {from_class} {rel_type} {to_class}: {rel_label}")
                else:
                    lines.append(f"    {from_class} {rel_type} {to_class}")
                
        return "\n".join(lines)
        
    def generate_sequence(
        self,
        participants: List[str],
        messages: List[tuple],
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
            if isinstance(participant, dict):
                participant_id = participant["id"]
                participant_label = participant.get("label", participant_id)
                lines.append(f"    participant {participant_id} as {participant_label}")
            else:
                participant_id = participant
                lines.append(f"    participant {participant_id}")
            
        # Add messages
        for message in messages:
            if isinstance(message, dict):
                from_participant = message["from"]
                to_participant = message["to"]
                message_text = message["text"]
                message_type = message.get("type", "->")
                activate = message.get("activate", False)
                deactivate = message.get("deactivate", False)
            else:
                # Support tuples/lists with variable lengths:
                # (from, to[, text[, type[, activate[, deactivate]]]])
                if not isinstance(message, (tuple, list)) or len(message) < 2:
                    # Invalid message structure; skip safely
                    continue
                from_participant = message[0]
                to_participant = message[1]
                message_text = message[2] if len(message) >= 3 else ""
                message_type = message[3] if len(message) >= 4 else ">>" if False else "->>"
                activate = bool(message[4]) if len(message) >= 5 else False
                deactivate = bool(message[5]) if len(message) >= 6 else False
            
            lines.append(f"    {from_participant}{message_type}{to_participant}: {message_text}")
            
            # Add optional activation/deactivation
            if activate:
                lines.append(f"    activate {to_participant}")
            if deactivate:
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
        
        return self.generate_from_template_impl(template, variables, config)

    def validate_diagram(self, definition: str, diagram_type: DiagramType) -> bool:
        """Validate a diagram definition.
        
        Args:
            definition: Diagram definition to validate
            diagram_type: Expected type of diagram
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - check if diagram starts with expected type
            definition = definition.strip()
            
            if diagram_type == DiagramType.FLOWCHART:
                # Check for basic syntax errors like unclosed brackets
                if definition.count('[') != definition.count(']'):
                    return False
                return definition.startswith("flowchart")
            elif diagram_type == DiagramType.SEQUENCE:
                # Check for missing participants - sequence diagrams without participants are invalid
                if "participant" not in definition:
                    return False
                return definition.startswith("sequenceDiagram")
            elif diagram_type == DiagramType.CLASS:
                return definition.startswith("classDiagram")
            
            return False
        except Exception:
            return False
    
    def save_diagram(self, metadata: DiagramMetadata, definition: str, path: Path) -> None:
        """Save a diagram to disk.
        
        Args:
            metadata: Diagram metadata
            definition: Diagram definition
            path: Path to save to
        """
        path.write_text(definition)

    def load_diagram(self, path: Path) -> tuple:
        """Load a diagram from disk.
        
        Args:
            path: Path to load from
            
        Returns:
            Tuple of (metadata, definition)
        """
        definition = path.read_text()
        meta = DiagramMetadata(
            name=path.stem,
            description="",
            type=DiagramType.FLOWCHART,
            version="0.1.0",
            author="",
            tags=[],
        )
        return meta, definition
            
    def generate_from_template_impl(
        self,
        template: Dict[str, Any],
        variables: Dict[str, Any],
        config: Optional[DiagramConfig],
    ) -> Optional[str]:
        """Internal implementation of template generation."""
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
            
        except Exception:
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
        with open(file_path, 'w') as f:
            json.dump(template, f, indent=2)
        self.templates[name] = template 