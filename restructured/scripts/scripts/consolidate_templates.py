#!/usr/bin/env python3
"""
Template Consolidation Script for MCP Project Orchestrator.

This script consolidates project and component templates from various sources into a standardized format
and stores them in the target project's templates directory.

Sources:
1. /home/sparrow/projects/mcp-servers/src/templates (if exists)
2. /home/sparrow/projects/mcp-project-orchestrator/component_templates.json
3. /home/sparrow/projects/mcp-prompts-template/templates (if exists)
4. /home/sparrow/mcp/data/templates (if exists)

Target:
/home/sparrow/projects/mcp-project-orchestrator/src/mcp_project_orchestrator/templates
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


# Source directories and files
SOURCES = [
    Path("/home/sparrow/projects/mcp-servers/src/templates"),
    Path("/home/sparrow/projects/mcp-project-orchestrator/component_templates.json"),
    Path("/home/sparrow/projects/mcp-prompts-template/templates"),
    Path("/home/sparrow/mcp/data/templates")
]

# Target directory
TARGET = Path("/home/sparrow/projects/mcp-project-orchestrator/src/mcp_project_orchestrator/templates")


def ensure_target_directory():
    """Ensure the target directory exists with required subdirectories."""
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "project").mkdir(exist_ok=True)
    (TARGET / "component").mkdir(exist_ok=True)


def get_template_files(source_dir: Path) -> List[Path]:
    """Get all template files from a source directory."""
    if not source_dir.exists():
        print(f"Source directory does not exist: {source_dir}")
        return []
        
    # Look for JSON files
    json_files = list(source_dir.glob("**/*.json"))
    
    # Look for YAML/YML files
    yaml_files = list(source_dir.glob("**/*.yaml")) + list(source_dir.glob("**/*.yml"))
    
    return json_files + yaml_files


def extract_component_templates(file_path: Path) -> List[Dict[str, Any]]:
    """Extract component templates from a component_templates.json file."""
    templates = []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        if file_path.name == "component_templates.json" and "component_templates" in data:
            # Process each component template
            for component in data["component_templates"]:
                # Create a standardized template
                template = {
                    "name": component["name"],
                    "description": component.get("description", ""),
                    "type": "component",
                    "files": component.get("files", []),
                    "dependencies": component.get("dependencies", []),
                    "variables": component.get("variables", {}),
                    "metadata": {
                        "source": str(file_path),
                        "imported": True
                    }
                }
                
                # Include mermaid diagram if present
                if "mermaid" in component and component["mermaid"]:
                    template["mermaid"] = component["mermaid"]
                    
                templates.append(template)
    
    except Exception as e:
        print(f"Error extracting component templates from {file_path}: {str(e)}")
    
    return templates


def extract_project_template(file_path: Path) -> Optional[Dict[str, Any]]:
    """Extract a project template from a file."""
    try:
        with open(file_path, 'r') as f:
            if file_path.suffix == '.json':
                data = json.load(f)
            else:
                # For simplicity, treat other files as JSON for now
                # In a real implementation, add YAML parsing for .yaml/.yml files
                data = json.load(f)
                
        # Determine if this is a project template
        if "type" in data and data["type"] == "project":
            return data
            
        # Check if this follows project template structure
        if "name" in data and "structure" in data:
            # Create a standardized template
            template = {
                "name": data["name"],
                "description": data.get("description", ""),
                "type": "project",
                "structure": data["structure"],
                "variables": data.get("variables", {}),
                "scripts": data.get("scripts", []),
                "metadata": {
                    "source": str(file_path),
                    "imported": True
                }
            }
            
            return template
                
    except Exception as e:
        print(f"Error extracting project template from {file_path}: {str(e)}")
        
    return None


def normalize_component_template(template: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a component template to the standard format."""
    # Create standardized template structure
    normalized = {
        "name": template["name"],
        "description": template.get("description", ""),
        "type": "component",
        "files": template.get("files", []),
        "dependencies": template.get("dependencies", []),
        "variables": template.get("variables", {}),
        "version": template.get("version", {
            "major": 1,
            "minor": 0,
            "patch": 0
        }),
        "metadata": template.get("metadata", {
            "imported": True
        })
    }
    
    # Include mermaid diagram if present
    if "mermaid" in template:
        normalized["mermaid"] = template["mermaid"]
    
    return normalized


def normalize_project_template(template: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a project template to the standard format."""
    # Create standardized template structure
    normalized = {
        "name": template["name"],
        "description": template.get("description", ""),
        "type": "project",
        "structure": template.get("structure", []),
        "variables": template.get("variables", {}),
        "scripts": template.get("scripts", []),
        "version": template.get("version", {
            "major": 1,
            "minor": 0,
            "patch": 0
        }),
        "metadata": template.get("metadata", {
            "imported": True
        })
    }
    
    return normalized


def save_template(template: Dict[str, Any]):
    """Save a normalized template to the target directory."""
    name = template["name"]
    template_type = template["type"]
    
    # Generate safe filename
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    
    # Save to both the main directory and the type-specific directory
    for save_path in [TARGET / f"{safe_name}.json", TARGET / template_type / f"{safe_name}.json"]:
        with open(save_path, 'w') as f:
            json.dump(template, f, indent=2)
            
    return safe_name


def process_all_sources():
    """Process all source files and consolidate templates."""
    ensure_target_directory()
    
    # Track processed templates by name and type
    processed = {
        "component": {},
        "project": {}
    }
    
    # Process each source
    for source in SOURCES:
        print(f"Processing source: {source}")
        
        if source.is_file() and source.suffix == '.json':
            # Handle component templates JSON file
            if source.name == "component_templates.json":
                templates = extract_component_templates(source)
                for template in templates:
                    name = template["name"]
                    if name in processed["component"]:
                        print(f"  Skipping duplicate component template: {name}")
                        continue
                    
                    normalized = normalize_component_template(template)
                    safe_name = save_template(normalized)
                    processed["component"][name] = safe_name
                    print(f"  Processed component template: {name} -> {safe_name}.json")
        
        elif source.is_dir():
            # Handle directories
            template_files = get_template_files(source)
            
            for file_path in template_files:
                # Try to extract as project template first
                project_template = extract_project_template(file_path)
                
                if project_template:
                    name = project_template["name"]
                    if name in processed["project"]:
                        print(f"  Skipping duplicate project template: {name}")
                        continue
                    
                    normalized = normalize_project_template(project_template)
                    safe_name = save_template(normalized)
                    processed["project"][name] = safe_name
                    print(f"  Processed project template: {name} -> {safe_name}.json")
                
                # If not a project template, check if it has component templates
                elif file_path.suffix == '.json':
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            
                        # Check if this contains component templates
                        if "component_templates" in data:
                            for component in data["component_templates"]:
                                template = {
                                    "name": component["name"],
                                    "description": component.get("description", ""),
                                    "type": "component",
                                    "files": component.get("files", []),
                                    "dependencies": component.get("dependencies", []),
                                    "variables": component.get("variables", {}),
                                    "metadata": {
                                        "source": str(file_path),
                                        "imported": True
                                    }
                                }
                                
                                # Include mermaid diagram if present
                                if "mermaid" in component and component["mermaid"]:
                                    template["mermaid"] = component["mermaid"]
                                
                                name = template["name"]
                                if name in processed["component"]:
                                    print(f"  Skipping duplicate component template: {name}")
                                    continue
                                
                                normalized = normalize_component_template(template)
                                safe_name = save_template(normalized)
                                processed["component"][name] = safe_name
                                print(f"  Processed component template: {name} -> {safe_name}.json")
                    
                    except Exception as e:
                        print(f"Error processing file {file_path}: {str(e)}")
    
    # Generate an index file
    index = {
        "component_templates": {
            "templates": list(processed["component"].keys()),
            "count": len(processed["component"])
        },
        "project_templates": {
            "templates": list(processed["project"].keys()),
            "count": len(processed["project"])
        }
    }
    
    # Save index file
    with open(TARGET / "index.json", 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\nConsolidation complete.")
    print(f"Component templates: {len(processed['component'])}")
    print(f"Project templates: {len(processed['project'])}")


if __name__ == "__main__":
    process_all_sources() 