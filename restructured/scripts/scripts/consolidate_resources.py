#!/usr/bin/env python3
"""
Resource Consolidation Script for MCP Project Orchestrator.

This script consolidates resources (documentation files, code snippets, configuration examples, etc.)
from various sources into a standardized format and stores them in the target project's resources directory.

Sources:
1. /home/sparrow/projects/mcp-servers/resources (if exists)
2. /home/sparrow/projects/mcp-servers/src/static (if exists)
3. /home/sparrow/mcp/data/resources (if exists)
4. /home/sparrow/mcp/docs (if exists)

Target:
/home/sparrow/projects/mcp-project-orchestrator/src/mcp_project_orchestrator/resources
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Set


# Source directories
SOURCES = [
    Path("/home/sparrow/projects/mcp-servers/resources"),
    Path("/home/sparrow/projects/mcp-servers/src/static"),
    Path("/home/sparrow/mcp/data/resources"),
    Path("/home/sparrow/mcp/docs")
]

# Target directory
TARGET = Path("/home/sparrow/projects/mcp-project-orchestrator/src/mcp_project_orchestrator/resources")

# Categories for organization
CATEGORIES = {
    "documentation": [".md", ".txt", ".pdf", ".html", ".docx"],
    "code_examples": [".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".sh", ".bash"],
    "config": [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"],
    "images": [".png", ".jpg", ".jpeg", ".gif", ".svg"],
    "other": []  # Fallback category
}


def ensure_target_directory():
    """Ensure the target directory exists with required subdirectories."""
    TARGET.mkdir(parents=True, exist_ok=True)
    
    # Create category subdirectories
    for category in CATEGORIES.keys():
        (TARGET / category).mkdir(exist_ok=True)


def get_category_for_file(file_path: Path) -> str:
    """Determine the appropriate category for a file based on its extension."""
    extension = file_path.suffix.lower()
    
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
            
    return "other"


def compute_file_hash(file_path: Path) -> str:
    """Compute a SHA-256 hash of a file to detect duplicates."""
    hash_obj = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
            
    return hash_obj.hexdigest()


def get_resource_files(source_dir: Path) -> List[Path]:
    """Get all resource files from a source directory."""
    if not source_dir.exists():
        print(f"Source directory does not exist: {source_dir}")
        return []
    
    # Get all files recursively
    files = []
    for item in source_dir.glob("**/*"):
        if item.is_file():
            files.append(item)
            
    return files


def process_resource_file(file_path: Path, processed_hashes: Set[str]) -> Optional[Dict[str, Any]]:
    """Process a resource file and return metadata if it's not a duplicate."""
    try:
        # Compute hash to detect duplicates
        file_hash = compute_file_hash(file_path)
        
        if file_hash in processed_hashes:
            print(f"  Skipping duplicate file: {file_path}")
            return None
            
        # Determine category
        category = get_category_for_file(file_path)
        
        # Create metadata
        metadata = {
            "name": file_path.name,
            "original_path": str(file_path),
            "category": category,
            "hash": file_hash,
            "size": file_path.stat().st_size
        }
        
        return metadata
        
    except Exception as e:
        print(f"Error processing resource file {file_path}: {str(e)}")
        return None


def save_resource_file(file_path: Path, metadata: Dict[str, Any]) -> str:
    """Save a resource file to the target directory."""
    category = metadata["category"]
    
    # Generate a safe filename to avoid conflicts
    base_name = file_path.stem
    extension = file_path.suffix
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in base_name)
    target_filename = f"{safe_name}{extension}"
    
    # Check if file already exists, append counter if needed
    counter = 1
    while (TARGET / category / target_filename).exists():
        target_filename = f"{safe_name}_{counter}{extension}"
        counter += 1
    
    # Copy the file
    target_path = TARGET / category / target_filename
    shutil.copy2(file_path, target_path)
    
    # Update metadata
    metadata["target_path"] = str(target_path)
    metadata["filename"] = target_filename
    
    return target_filename


def process_all_sources():
    """Process all source directories and consolidate resources."""
    ensure_target_directory()
    
    # Track processed files by hash to avoid duplicates
    processed_hashes = set()
    processed_files = {category: [] for category in CATEGORIES.keys()}
    
    # Process each source
    for source_dir in SOURCES:
        print(f"Processing source: {source_dir}")
        resource_files = get_resource_files(source_dir)
        
        for file_path in resource_files:
            metadata = process_resource_file(file_path, processed_hashes)
            
            if metadata:
                # Save the file
                target_filename = save_resource_file(file_path, metadata)
                
                # Update tracking
                processed_hashes.add(metadata["hash"])
                processed_files[metadata["category"]].append(metadata)
                
                print(f"  Processed resource: {file_path.name} -> {metadata['category']}/{target_filename}")
    
    # Generate an index file
    index = {
        "categories": {},
        "total_count": sum(len(files) for files in processed_files.values())
    }
    
    # Build category index
    for category, files in processed_files.items():
        index["categories"][category] = {
            "files": [f["filename"] for f in files],
            "count": len(files)
        }
        
        # Save category index file
        with open(TARGET / category / "index.json", 'w') as f:
            json.dump({
                "files": files,
                "count": len(files)
            }, f, indent=2)
    
    # Save main index file
    with open(TARGET / "index.json", 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\nConsolidation complete. Processed {index['total_count']} resource files.")
    for category, info in index["categories"].items():
        if info["count"] > 0:
            print(f"{category}: {info['count']} files")


if __name__ == "__main__":
    process_all_sources() 