#!/usr/bin/env python3
"""
Environment Verification Script for MCP Project Orchestrator

This script checks that the environment is correctly configured for running
the MCP Project Orchestrator, verifying dependencies, file structure, and
configurations.
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path
import json

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# Required directories
REQUIRED_DIRS = [
    "src/mcp_project_orchestrator",
    "src/mcp_project_orchestrator/core",
    "src/mcp_project_orchestrator/prompt_manager",
    "src/mcp_project_orchestrator/mermaid",
    "src/mcp_project_orchestrator/templates",
    "src/mcp_project_orchestrator/prompts",
    "src/mcp_project_orchestrator/resources",
    "src/mcp_project_orchestrator/cli",
    "src/mcp_project_orchestrator/utils",
    "tests",
    "tests/integration",
    "config",
    "docs",
    "scripts",
]

# Required dependencies
REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "jinja2",
    "pydantic",
    "python-dotenv",
    "aiofiles",
    "pyyaml",
    "jsonschema",
    "rich",
    "typer",
    "python-multipart",
    "requests",
    "aiohttp",
    "watchdog",
    "markdown",
    "pygments",
]

def print_status(message, status, details=None):
    """Print a formatted status message."""
    if status == "OK":
        print(f"{GREEN}[✓] {message}{RESET}")
    elif status == "WARNING":
        print(f"{YELLOW}[!] {message}{RESET}")
        if details:
            print(f"   {details}")
    elif status == "ERROR":
        print(f"{RED}[✗] {message}{RESET}")
        if details:
            print(f"   {details}")
    else:
        print(f"[-] {message}")

def check_directory_structure():
    """Check that all required directories exist."""
    print("\nChecking directory structure...")
    all_ok = True
    
    for directory in REQUIRED_DIRS:
        path = Path(directory)
        if path.exists() and path.is_dir():
            print_status(f"Directory {directory} exists", "OK")
        else:
            print_status(f"Directory {directory} is missing", "ERROR")
            all_ok = False
    
    return all_ok

def check_dependencies():
    """Check that all required packages are installed."""
    print("\nChecking dependencies...")
    all_ok = True
    
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
            print_status(f"Package {package} is installed", "OK")
        except ImportError:
            print_status(f"Package {package} is not installed", "ERROR")
            all_ok = False
    
    return all_ok

def check_config_files():
    """Check that the configuration files exist and are valid."""
    print("\nChecking configuration files...")
    
    # Check project_orchestration.json
    try:
        with open("project_orchestration.json", "r") as f:
            config = json.load(f)
        print_status("project_orchestration.json is valid JSON", "OK")
    except FileNotFoundError:
        print_status("project_orchestration.json not found", "ERROR")
        return False
    except json.JSONDecodeError as e:
        print_status("project_orchestration.json is not valid JSON", "ERROR", str(e))
        return False
    
    # Check project_templates.json
    try:
        with open("project_templates.json", "r") as f:
            templates = json.load(f)
        print_status("project_templates.json is valid JSON", "OK")
    except FileNotFoundError:
        print_status("project_templates.json not found", "ERROR")
        return False
    except json.JSONDecodeError as e:
        print_status("project_templates.json is not valid JSON", "ERROR", str(e))
        return False
    
    # Check component_templates.json if it exists
    if os.path.exists("component_templates.json"):
        try:
            with open("component_templates.json", "r") as f:
                components = json.load(f)
            print_status("component_templates.json is valid JSON", "OK")
        except json.JSONDecodeError as e:
            print_status("component_templates.json is not valid JSON", "ERROR", str(e))
            return False
    
    return True

def check_tests():
    """Run tests to verify everything works correctly."""
    print("\nChecking tests...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-xvs", "tests/"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print_status("All tests passed", "OK")
            return True
        else:
            print_status("Some tests failed", "ERROR", result.stderr)
            return False
    except Exception as e:
        print_status("Error running tests", "ERROR", str(e))
        return False

def check_git_status():
    """Check git status to ensure everything is committed."""
    print("\nChecking git status...")
    
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            print_status(
                "There are uncommitted changes", 
                "WARNING", 
                "Consider committing changes before deployment"
            )
        else:
            print_status("Working directory is clean", "OK")
        
        # Check if ahead of remote
        result = subprocess.run(
            ["git", "status", "-sb"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if "ahead" in result.stdout:
            print_status(
                "Local branch is ahead of remote", 
                "WARNING", 
                "Consider pushing commits before deployment"
            )
        
        return True
    except Exception as e:
        print_status("Error checking git status", "ERROR", str(e))
        return False

def main():
    """Main function to run all checks."""
    print("=== MCP Project Orchestrator Environment Verification ===")
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Dependencies", check_dependencies),
        ("Configuration Files", check_config_files),
        ("Git Status", check_git_status),
        ("Tests", check_tests),
    ]
    
    all_passed = True
    results = {}
    
    for name, check_func in checks:
        result = check_func()
        results[name] = result
        if not result:
            all_passed = False
    
    print("\n=== Verification Summary ===")
    for name, result in results.items():
        status = "OK" if result else "ERROR"
        print_status(name, status)
    
    if all_passed:
        print(f"\n{GREEN}All checks passed! The environment is ready for deployment.{RESET}")
        return 0
    else:
        print(f"\n{RED}Some checks failed. Please fix the issues before deployment.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 