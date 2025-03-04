#!/usr/bin/env python3
"""
Claude Desktop Integration Setup Script

This script helps with setting up the MCP Project Orchestrator
for use with Claude Desktop by generating the correct configuration
and ensuring the package is properly installed.
"""
import os
import sys
import json
import argparse
import subprocess
import platform


def get_claude_config_path():
    """Get the path to the Claude Desktop config file based on the OS."""
    if platform.system() == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    elif platform.system() == "Windows":
        return os.path.join(os.environ["APPDATA"], "Claude", "claude_desktop_config.json")
    else:
        return os.path.expanduser("~/.config/Claude/claude_desktop_config.json")


def load_existing_config(config_path):
    """Load existing Claude Desktop config if it exists."""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Existing config at {config_path} is not valid JSON. Creating new config.")
    return {"mcpServers": {}}


def save_config(config, config_path):
    """Save the configuration to the Claude Desktop config file."""
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {config_path}")


def setup_python_config(project_path):
    """Set up the configuration for Python-based integration."""
    return {
        "command": "python",
        "args": [
            "-m",
            "mcp_project_orchestrator.fastmcp"
        ],
        "env": {
            "PYTHONPATH": project_path
        }
    }


def setup_docker_config(image_name):
    """Set up the configuration for Docker-based integration."""
    return {
        "command": "docker",
        "args": [
            "run",
            "--rm",
            "-p",
            "8080:8080",
            image_name
        ]
    }


def setup_podman_config(image_name):
    """Set up the configuration for Podman-based integration."""
    return {
        "command": "podman",
        "args": [
            "run",
            "--rm",
            "-p",
            "8080:8080",
            image_name
        ]
    }


def check_prerequisites(method):
    """Check if the required tools are installed."""
    if method == "python":
        try:
            subprocess.run(["python", "--version"], check=True, stdout=subprocess.PIPE)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Error: Python is not installed or not in PATH.")
            return False
    elif method == "docker":
        try:
            subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Error: Docker is not installed or not in PATH.")
            return False
    elif method == "podman":
        try:
            subprocess.run(["podman", "--version"], check=True, stdout=subprocess.PIPE)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Error: Podman is not installed or not in PATH.")
            return False
    return False


def main():
    """Main function to set up the Claude Desktop integration."""
    parser = argparse.ArgumentParser(
        description="Set up MCP Project Orchestrator for Claude Desktop"
    )
    parser.add_argument(
        "--method", 
        choices=["python", "docker", "podman"], 
        default="python",
        help="Integration method (default: python)"
    )
    parser.add_argument(
        "--image", 
        help="Docker/Podman image name for container-based integration"
    )
    parser.add_argument(
        "--project-path", 
        default=os.getcwd(),
        help="Path to the mcp-project-orchestrator directory (default: current directory)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080,
        help="Port to use for the MCP server (default: 8080)"
    )
    
    args = parser.parse_args()
    
    # Check prerequisites
    if not check_prerequisites(args.method):
        return 1
    
    # Get the Claude Desktop config path
    config_path = get_claude_config_path()
    
    # Load existing config or create new one
    config = load_existing_config(config_path)
    
    # Set up the configuration based on the chosen method
    if args.method == "python":
        server_config = setup_python_config(args.project_path)
    elif args.method == "docker":
        image_name = args.image or "mcp-project-orchestrator:latest"
        server_config = setup_docker_config(image_name)
    elif args.method == "podman":
        image_name = args.image or "localhost/mcp-project-orchestrator:latest"
        server_config = setup_podman_config(image_name)
    
    # Update port if needed
    if args.port != 8080:
        if args.method in ["docker", "podman"]:
            port_arg_index = server_config["args"].index("-p") + 1
            server_config["args"][port_arg_index] = f"{args.port}:8080"
    
    # Update the config
    config["mcpServers"]["project-orchestrator"] = server_config
    
    # Save the config
    save_config(config, config_path)
    
    print("\nSetup complete! Please restart Claude Desktop to access the MCP Project Orchestrator.")
    print("\nIf you encounter issues:")
    print(f"- Check the logs at {os.path.dirname(config_path)}/logs/mcp-server-project-orchestrator.log")
    print("- Make sure the MCP server is not already running on the same port")
    print("- Verify that Claude Desktop has the necessary permissions")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 