#!/usr/bin/env python3
"""
Prompt Template Consolidation Script for MCP Project Orchestrator.

This script consolidates prompt templates from various sources into a standardized format
and stores them in the target project's prompts directory.

Sources:
1. /home/sparrow/projects/mcp-prompts (if exists)
2. /home/sparrow/projects/mcp-servers/src/prompt-manager (if exists)
3. /home/sparrow/mcp/data/prompts (if exists)
4. /home/sparrow/mcp/prompts (if exists)

Target:
/home/sparrow/projects/mcp-project-orchestrator/src/mcp_project_orchestrator/prompts
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import re


# Source directories
SOURCES = [
    Path("/home/sparrow/projects/mcp-prompts"),
    Path("/home/sparrow/projects/mcp-servers/src/prompt-manager"),
    Path("/home/sparrow/mcp/data/prompts"),
    Path("/home/sparrow/mcp/prompts")
]

# Target directory
TARGET = Path("/home/sparrow/projects/mcp-project-orchestrator/src/mcp_project_orchestrator/prompts")

# Categories for organization
CATEGORIES = [
    "system",
    "user",
    "assistant",
    "general",
    "coding",
    "analysis",
    "architecture",
    "devops",
    "development",
    "other"  # Fallback category
]


def ensure_target_directory():
    """Ensure the target directory exists with required subdirectories."""
    TARGET.mkdir(parents=True, exist_ok=True)
    
    # Create category subdirectories
    for category in CATEGORIES:
        (TARGET / category).mkdir(exist_ok=True)


def get_prompt_files(source_dir: Path) -> List[Path]:
    """Get all prompt template files from a source directory."""
    if not source_dir.exists():
        print(f"Source directory does not exist: {source_dir}")
        return []
        
    # Look for JSON files
    json_files = list(source_dir.glob("**/*.json"))
    
    # Look for JavaScript files (often used for prompt templates)
    js_files = list(source_dir.glob("**/*.js"))
    
    # Look for TypeScript files
    ts_files = list(source_dir.glob("**/*.ts"))
    
    return json_files + js_files + ts_files


def extract_category_from_path(file_path: Path) -> str:
    """Try to determine the category from the file path."""
    path_str = str(file_path).lower()
    
    for category in CATEGORIES[:-1]:  # Exclude the fallback category
        if category in path_str:
            return category
            
    # If we can't determine from path, try to analyze the content later
    return "other"


def extract_template_from_js_ts(file_path: Path) -> Optional[Dict[str, Any]]:
    """Extract prompt template from a JavaScript or TypeScript file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Look for template content
        template_match = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*[`\'"]([^`\'"]+)[`\'"]', content)
        if template_match:
            template_name = template_match.group(1)
            template_content = template_match.group(2)
            
            # Look for export statement to get a better name
            export_match = re.search(r'export\s+(?:const|let|var)\s+(\w+)', content)
            if export_match:
                template_name = export_match.group(1)
                
            # Determine category from content keywords
            category = "other"
            if "system:" in content.lower() or "system message" in content.lower():
                category = "system"
            elif "user:" in content.lower() or "user message" in content.lower():
                category = "user"
            elif "assistant:" in content.lower() or "assistant message" in content.lower():
                category = "assistant"
            elif "code" in content.lower() or "function" in content.lower() or "class" in content.lower():
                category = "coding"
            elif "analyze" in content.lower() or "analysis" in content.lower():
                category = "analysis"
                
            return {
                "name": template_name,
                "description": f"Prompt template extracted from {file_path.name}",
                "type": "prompt",
                "category": category,
                "content": template_content,
                "variables": {},
                "metadata": {
                    "source": str(file_path),
                    "imported": True
                }
            }
            
        return None
        
    except Exception as e:
        print(f"Error extracting template from {file_path}: {str(e)}")
        return None


def extract_template_from_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Extract prompt template from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Check if this is already a prompt template
        if "name" in data and ("content" in data or "template" in data):
            template = {
                "name": data["name"],
                "description": data.get("description", f"Prompt template imported from {file_path.name}"),
                "type": "prompt",
                "category": data.get("category", extract_category_from_path(file_path)),
                "content": data.get("content", data.get("template", "")),
                "variables": data.get("variables", {}),
                "metadata": {
                    "source": str(file_path),
                    "imported": True
                }
            }
            
            return template
            
        # If not a standard format, try to extract content
        elif "prompt" in data:
            return {
                "name": file_path.stem,
                "description": data.get("description", f"Prompt template imported from {file_path.name}"),
                "type": "prompt",
                "category": data.get("category", extract_category_from_path(file_path)),
                "content": data["prompt"],
                "variables": data.get("variables", {}),
                "metadata": {
                    "source": str(file_path),
                    "imported": True
                }
            }
            
        # If just a simple prompt object
        elif isinstance(data, str):
            return {
                "name": file_path.stem,
                "description": f"Prompt template imported from {file_path.name}",
                "type": "prompt",
                "category": extract_category_from_path(file_path),
                "content": data,
                "variables": {},
                "metadata": {
                    "source": str(file_path),
                    "imported": True
                }
            }
            
        return None
        
    except Exception as e:
        print(f"Error extracting template from {file_path}: {str(e)}")
        return None


def normalize_template(file_path: Path) -> Optional[Dict[str, Any]]:
    """Convert a template file into a standardized format."""
    if file_path.suffix == '.json':
        return extract_template_from_json(file_path)
    elif file_path.suffix in ['.js', '.ts']:
        return extract_template_from_js_ts(file_path)
    else:
        print(f"Unsupported file type: {file_path}")
        return None


def save_template(template: Dict[str, Any]):
    """Save a normalized template to the target directory."""
    name = template["name"]
    category = template["category"]
    
    # Generate safe filename
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    
    # Save to both the main directory and the category directory
    for save_path in [TARGET / f"{safe_name}.json", TARGET / category / f"{safe_name}.json"]:
        with open(save_path, 'w') as f:
            json.dump(template, f, indent=2)
            
    return safe_name


def process_all_sources():
    """Process all source files and consolidate prompt templates."""
    ensure_target_directory()
    
    # Track processed templates by name
    processed = {}
    
    # Process each source
    for source in SOURCES:
        print(f"Processing source: {source}")
        
        if not source.exists():
            print(f"  Source directory does not exist: {source}")
            continue
            
        # Get all template files
        template_files = get_prompt_files(source)
        
        for file_path in template_files:
            # Normalize the template
            template = normalize_template(file_path)
            
            if template:
                name = template["name"]
                if name in processed:
                    print(f"  Skipping duplicate template: {name}")
                    continue
                
                # Save the template
                safe_name = save_template(template)
                processed[name] = {
                    "filename": safe_name,
                    "category": template["category"]
                }
                
                print(f"  Processed template: {name} -> {template['category']}/{safe_name}.json")
    
    # Generate an index file
    index = {
        "templates": {},
        "categories": {},
        "total_count": len(processed)
    }
    
    # Build main index
    for name, info in processed.items():
        index["templates"][name] = info
    
    # Build category index
    for category in CATEGORIES:
        category_templates = [name for name, info in processed.items() if info["category"] == category]
        index["categories"][category] = {
            "templates": category_templates,
            "count": len(category_templates)
        }
        
        # Save category index file
        with open(TARGET / category / "index.json", 'w') as f:
            json.dump({
                "templates": category_templates,
                "count": len(category_templates)
            }, f, indent=2)
    
    # Save main index file
    with open(TARGET / "index.json", 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\nConsolidation complete. Processed {len(processed)} templates.")
    for category in CATEGORIES:
        count = index["categories"][category]["count"]
        if count > 0:
            print(f"{category}: {count} templates")


if __name__ == "__main__":
    process_all_sources() 