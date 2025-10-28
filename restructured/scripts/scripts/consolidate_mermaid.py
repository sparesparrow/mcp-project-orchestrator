#!/usr/bin/env python3
"""
Mermaid Template Consolidation Script for MCP Project Orchestrator.

This script consolidates Mermaid diagram templates from various sources into a standardized format
and stores them in the target project's mermaid directory.

Sources:
1. /home/sparrow/projects/mcp-servers/src/mermaid
2. Component templates in /home/sparrow/projects/mcp-project-orchestrator/component_templates.json
3. Mermaid templates from /home/sparrow/mcp/data/prompts

Target:
/home/sparrow/projects/mcp-project-orchestrator/src/mcp_project_orchestrator/mermaid/templates
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


# Source directories and files
SOURCES = [
    Path("/home/sparrow/projects/mcp-servers/src/mermaid/demo_output"),
    Path("/home/sparrow/projects/mcp-servers/src/mermaid"),
    Path("/home/sparrow/projects/mcp-project-orchestrator/component_templates.json"),
    Path("/home/sparrow/mcp/data/prompts")
]

# Target directory
TARGET = Path("/home/sparrow/projects/mcp-project-orchestrator/src/mcp_project_orchestrator/mermaid/templates")


def ensure_target_directory():
    """Ensure the target directory exists."""
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "flowchart").mkdir(exist_ok=True)
    (TARGET / "class").mkdir(exist_ok=True)
    (TARGET / "sequence").mkdir(exist_ok=True)
    (TARGET / "er").mkdir(exist_ok=True)
    (TARGET / "gantt").mkdir(exist_ok=True)
    (TARGET / "pie").mkdir(exist_ok=True)


def get_mermaid_files(source_dir: Path) -> List[Path]:
    """Get all mermaid diagram files from a source directory."""
    if not source_dir.exists():
        print(f"Source directory does not exist: {source_dir}")
        return []
        
    # Look for mermaid diagram files
    extensions = [".mmd", ".mermaid", ".md"]
    
    files = []
    for ext in extensions:
        files.extend(list(source_dir.glob(f"**/*{ext}")))
    
    # Also look for specific Mermaid JSON files
    json_files = [
        f for f in source_dir.glob("**/*.json") 
        if "mermaid" in f.stem.lower() or "diagram" in f.stem.lower()
    ]
    
    return files + json_files


def extract_mermaid_from_json(file_path: Path) -> List[Dict[str, Any]]:
    """Extract mermaid templates from JSON files."""
    templates = []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Handle component templates format
        if file_path.name == "component_templates.json" and "component_templates" in data:
            for component in data["component_templates"]:
                if "mermaid" in component and component["mermaid"]:
                    # Extract the mermaid prompt as a template
                    templates.append({
                        "name": f"{component['name']}-diagram",
                        "description": f"Mermaid diagram for {component['name']} pattern",
                        "type": "flowchart",  # Default to flowchart
                        "content": component["mermaid"],
                        "variables": {}
                    })
        
        # Handle mermaid diagram templates in prompts
        elif "template" in data or "content" in data:
            content = data.get("template", data.get("content", ""))
            if "mermaid" in content.lower() or "flowchart" in content.lower() or "classDiagram" in content.lower():
                templates.append({
                    "name": data.get("name", file_path.stem),
                    "description": data.get("description", ""),
                    "type": detect_diagram_type(content),
                    "content": content,
                    "variables": data.get("variables", {})
                })
    
    except Exception as e:
        print(f"Error extracting mermaid from {file_path}: {str(e)}")
    
    return templates


def extract_mermaid_from_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Extract mermaid diagram from a file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Detect diagram type
        diagram_type = detect_diagram_type(content)
        
        return {
            "name": file_path.stem,
            "description": f"Mermaid {diagram_type} diagram",
            "type": diagram_type,
            "content": content,
            "variables": {}
        }
    
    except Exception as e:
        print(f"Error reading mermaid file {file_path}: {str(e)}")
        return None


def detect_diagram_type(content: str) -> str:
    """Detect the type of mermaid diagram from content."""
    content = content.lower()
    
    if "flowchart" in content or "graph " in content:
        return "flowchart"
    elif "classDiagram" in content:
        return "class"
    elif "sequenceDiagram" in content:
        return "sequence"
    elif "erDiagram" in content:
        return "er"
    elif "gantt" in content:
        return "gantt"
    elif "pie" in content:
        return "pie"
    else:
        return "flowchart"  # Default


def normalize_template(template: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a mermaid template to the standard format."""
    # Create standardized template structure
    normalized = {
        "name": template["name"],
        "description": template.get("description", ""),
        "type": template.get("type", "flowchart"),
        "content": template.get("content", ""),
        "variables": template.get("variables", {}),
        "metadata": {
            "imported": True
        }
    }
    
    return normalized


def save_template(template: Dict[str, Any]):
    """Save a normalized template to the target directory."""
    name = template["name"]
    diagram_type = template["type"]
    
    # Generate safe filename
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    
    # Save to both the main directory and the type-specific directory
    for save_path in [TARGET / f"{safe_name}.json", TARGET / diagram_type / f"{safe_name}.json"]:
        with open(save_path, 'w') as f:
            json.dump(template, f, indent=2)
            
    return safe_name


def process_all_sources():
    """Process all source files and consolidate mermaid templates."""
    ensure_target_directory()
    
    # Track processed templates by name
    processed = {}
    
    # Process each source
    for source in SOURCES:
        print(f"Processing source: {source}")
        
        if source.is_file() and source.suffix == '.json':
            # Handle JSON files directly
            templates = extract_mermaid_from_json(source)
            for template in templates:
                name = template["name"]
                if name in processed:
                    print(f"  Skipping duplicate template: {name}")
                    continue
                
                normalized = normalize_template(template)
                safe_name = save_template(normalized)
                processed[name] = safe_name
                print(f"  Processed template: {name} -> {safe_name}.json")
        
        elif source.is_dir():
            # Handle directories
            mermaid_files = get_mermaid_files(source)
            
            for file_path in mermaid_files:
                if file_path.suffix == '.json':
                    templates = extract_mermaid_from_json(file_path)
                    for template in templates:
                        name = template["name"]
                        if name in processed:
                            print(f"  Skipping duplicate template: {name}")
                            continue
                        
                        normalized = normalize_template(template)
                        safe_name = save_template(normalized)
                        processed[name] = safe_name
                        print(f"  Processed JSON template: {name} -> {safe_name}.json")
                else:
                    # Handle mermaid files directly
                    template = extract_mermaid_from_file(file_path)
                    if template:
                        name = template["name"]
                        if name in processed:
                            print(f"  Skipping duplicate template: {name}")
                            continue
                        
                        normalized = normalize_template(template)
                        safe_name = save_template(normalized)
                        processed[name] = safe_name
                        print(f"  Processed mermaid file: {name} -> {safe_name}.json")
    
    # Generate an index file
    index = {
        "templates": list(processed.keys()),
        "count": len(processed),
        "types": {}
    }
    
    # Build type index
    type_dirs = TARGET.glob("*")
    for type_dir in [d for d in type_dirs if d.is_dir()]:
        type_name = type_dir.name
        templates = list(type_dir.glob("*.json"))
        index["types"][type_name] = {
            "templates": [t.stem for t in templates],
            "count": len(templates)
        }
    
    # Save index file
    with open(TARGET / "index.json", 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\nConsolidation complete. Processed {len(processed)} templates.")
    print(f"Types: {', '.join(index['types'].keys())}")


if __name__ == "__main__":
    process_all_sources() 