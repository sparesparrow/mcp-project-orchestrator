#!/bin/bash
# MCP Test Script - Run all the key commands to test the MCP server

set -e

CONTAINER_ENGINE=${1:-docker}
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_GREEN}=== MCP Project Orchestrator Testing Script ===${COLOR_RESET}"
echo "Using container engine: $CONTAINER_ENGINE"

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Project directory: $PROJECT_DIR"

# Check container engine
if ! command -v $CONTAINER_ENGINE &> /dev/null; then
    echo -e "${COLOR_RED}Error: $CONTAINER_ENGINE not found${COLOR_RESET}"
    exit 1
fi

# Check if Node.js and npm are installed
if ! command -v npm &> /dev/null; then
    echo -e "${COLOR_RED}Error: npm not found. Please install Node.js${COLOR_RESET}"
    exit 1
fi

# Stop any existing containers
echo -e "\n${COLOR_GREEN}Stopping any existing MCP containers...${COLOR_RESET}"
$CONTAINER_ENGINE stop mcp-server &>/dev/null || true
$CONTAINER_ENGINE rm mcp-server &>/dev/null || true

# Build the container
echo -e "\n${COLOR_GREEN}Building container image...${COLOR_RESET}"
$CONTAINER_ENGINE build -t mcp-project-orchestrator:latest -f Containerfile .

# Run the container with volume mounting
echo -e "\n${COLOR_GREEN}Starting MCP server with volume mounting...${COLOR_RESET}"
if [ "$CONTAINER_ENGINE" == "docker" ]; then
    $CONTAINER_ENGINE run -d --rm -p 8080:8080 \
      -v "$PROJECT_DIR:/app" \
      --workdir /app \
      --entrypoint python \
      --name mcp-server \
      mcp-project-orchestrator:latest \
      -m mcp_project_orchestrator.fastmcp
else
    $CONTAINER_ENGINE run -d --rm -p 8080:8080 \
      -v "$PROJECT_DIR:/app:Z" \
      --workdir /app \
      --entrypoint python \
      --name mcp-server \
      localhost/mcp-project-orchestrator:latest \
      -m mcp_project_orchestrator.fastmcp
fi

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Install MCP Inspector if needed
echo -e "\n${COLOR_GREEN}Setting up MCP Inspector...${COLOR_RESET}"
npm list -g @modelcontextprotocol/inspector &>/dev/null || npm install -g @modelcontextprotocol/inspector

# Run basic test
echo -e "\n${COLOR_GREEN}Running basic connectivity test...${COLOR_RESET}"
npx @modelcontextprotocol/inspector http://localhost:8080 || { 
    echo -e "${COLOR_RED}Basic test failed${COLOR_RESET}"; 
    $CONTAINER_ENGINE stop mcp-server; 
    exit 1; 
}

# Run validation
echo -e "\n${COLOR_GREEN}Running validation test...${COLOR_RESET}"
npx @modelcontextprotocol/inspector http://localhost:8080 --validate || { 
    echo -e "${COLOR_RED}Validation test failed${COLOR_RESET}"; 
    $CONTAINER_ENGINE stop mcp-server; 
    exit 1; 
}

# Stop the container
echo -e "\n${COLOR_GREEN}Tests completed successfully. Stopping container...${COLOR_RESET}"
$CONTAINER_ENGINE stop mcp-server

echo -e "\n${COLOR_GREEN}All tests passed!${COLOR_RESET}"
echo -e "For interactive testing, run:"
echo -e "  $CONTAINER_ENGINE run -d --rm -p 8080:8080 -v \"$PROJECT_DIR:/app$([ \"$CONTAINER_ENGINE\" = \"podman\" ] && echo ':Z')\" --workdir /app --entrypoint python $([ \"$CONTAINER_ENGINE\" = \"podman\" ] && echo \"localhost/\")mcp-project-orchestrator:latest -m mcp_project_orchestrator.fastmcp"
echo -e "  npx @modelcontextprotocol/inspector http://localhost:8080 --interactive" 