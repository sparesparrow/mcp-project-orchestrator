#!/bin/bash
# Special script to set up Claude Desktop to use the Podman container with proper volume mounts

# Determine config path based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32" ]]; then
    CONFIG_PATH="$APPDATA/Claude/claude_desktop_config.json"
else
    CONFIG_PATH="$HOME/.config/Claude/claude_desktop_config.json"
fi

echo "Claude Desktop config path: $CONFIG_PATH"

# Get the current directory path
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Project directory: $PROJECT_DIR"

# Create config directory if it doesn't exist
mkdir -p "$(dirname "$CONFIG_PATH")"

# Create or update the configuration
cat > "$CONFIG_PATH" << EOL
{
  "mcpServers": {
    "project-orchestrator": {
      "command": "podman",
      "args": [
        "run",
        "--rm",
        "-p",
        "8080:8080",
        "-v",
        "${PROJECT_DIR}:/app:Z",
        "--workdir",
        "/app",
        "--entrypoint",
        "python",
        "localhost/mcp-project-orchestrator:latest",
        "-m",
        "mcp_project_orchestrator.fastmcp"
      ]
    }
  }
}
EOL

echo "Configuration saved to $CONFIG_PATH"
echo "Please restart Claude Desktop to apply the changes."
echo 
echo "If you still encounter issues, try:"
echo "1. Rebuild the container: podman build -t mcp-project-orchestrator:latest -f Containerfile ."
echo "2. Test it directly: podman run --rm -v \"${PROJECT_DIR}:/app:Z\" --workdir /app -p 8080:8080 --entrypoint python localhost/mcp-project-orchestrator:latest -m mcp_project_orchestrator.fastmcp"
echo "3. Check the logs: ls -la ~/Library/Logs/Claude/mcp-server-project-orchestrator.log" 