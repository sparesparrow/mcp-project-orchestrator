#!/bin/bash
# MCP Project Orchestrator - Unified Testing Script
# Consolidates multiple testing scripts for easier testing

set -e

# Color definitions
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

# Get script and project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_DATA_DIR="/home/sparrow/mcp/data"
CLAUDE_CONFIG_DIR="$HOME/.config/Claude"
CLAUDE_LOG_DIR="$CLAUDE_CONFIG_DIR/logs"

# Default values
CONTAINER_ENGINE="docker"
TEST_TYPE=""
INTERACTIVE=false
SKIP_DB_INIT=false
CLAUDE_DESKTOP_BIN="$HOME/bin/run-claude.sh"

# Function to display help message
display_help() {
  echo "MCP Project Orchestrator - Unified Testing Script"
  echo
  echo "Usage: $0 [options]"
  echo
  echo "Options:"
  echo "  --basic            Run basic MCP server tests"
  echo "  --claude-desktop   Test Claude Desktop integration"
  echo "  --docker           Use Docker for container operations (default)"
  echo "  --podman           Use Podman for container operations"
  echo "  --interactive      Run in interactive mode"
  echo "  --skip-db-init     Skip database initialization"
  echo "  --help             Display this help message"
  echo
}

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --basic)
      TEST_TYPE="basic"
      shift
      ;;
    --claude-desktop)
      TEST_TYPE="claude-desktop"
      shift
      ;;
    --docker)
      CONTAINER_ENGINE="docker"
      shift
      ;;
    --podman)
      CONTAINER_ENGINE="podman"
      shift
      ;;
    --interactive)
      INTERACTIVE=true
      shift
      ;;
    --skip-db-init)
      SKIP_DB_INIT=true
      shift
      ;;
    --help)
      display_help
      exit 0
      ;;
    *)
      echo -e "${COLOR_RED}Unknown option: $1${COLOR_RESET}"
      display_help
      exit 1
      ;;
  esac
done

# If no test type specified, ask the user
if [ -z "$TEST_TYPE" ]; then
  echo "Please select test type:"
  echo "1) Basic MCP server tests"
  echo "2) Claude Desktop integration tests"
  echo "3) Exit"
  
  read -p "Enter your choice (1-3): " choice
  
  case "$choice" in
    1)
      TEST_TYPE="basic"
      ;;
    2)
      TEST_TYPE="claude-desktop"
      ;;
    3)
      echo "Exiting..."
      exit 0
      ;;
    *)
      echo -e "${COLOR_RED}Invalid choice. Exiting.${COLOR_RESET}"
      exit 1
      ;;
  esac
fi

# Function to check if container is running
check_container_running() {
  local container_name="$1"
  if $CONTAINER_ENGINE ps --filter "name=$container_name" --format "{{.Names}}" | grep -q "$container_name"; then
    echo -e "${COLOR_GREEN}✅ Container '$container_name' is running${COLOR_RESET}"
    return 0
  else
    echo -e "${COLOR_RED}❌ Container '$container_name' is NOT running${COLOR_RESET}"
    return 1
  fi
}

# Function to clean up existing containers
cleanup_containers() {
  echo -e "${COLOR_GREEN}Cleaning up existing containers...${COLOR_RESET}"
  
  # List of containers to clean up
  containers=(
    "mcp-postgres-db-container"
    "pgai-vectorizer-worker"
    "mcp-prompt-manager-py"
    "mcp-prompts-sse"
    "mcp-prompts-stdio"
    "mcp-postgres-server"
    "mcp-server"
  )
  
  for container in "${containers[@]}"; do
    echo "Stopping and removing container: $container"
    $CONTAINER_ENGINE stop "$container" 2>/dev/null || true
    $CONTAINER_ENGINE rm "$container" 2>/dev/null || true
  done
}

# Function to initialize PostgreSQL
initialize_postgres() {
  if [ "$SKIP_DB_INIT" = true ]; then
    echo -e "${COLOR_YELLOW}Skipping PostgreSQL initialization as requested${COLOR_RESET}"
    return 0
  fi
  
  echo -e "${COLOR_GREEN}Initializing PostgreSQL...${COLOR_RESET}"
  "$SCRIPT_DIR/setup_mcp.sh" --db-only
}

# Function to check Claude Desktop logs
check_claude_logs() {
  echo -e "${COLOR_GREEN}Checking Claude Desktop logs...${COLOR_RESET}"
  
  if [ ! -d "$CLAUDE_LOG_DIR" ]; then
    echo -e "${COLOR_YELLOW}No Claude Desktop logs found at $CLAUDE_LOG_DIR${COLOR_RESET}"
    return 0
  fi
  
  local error_count=$(grep -r "ERROR" "$CLAUDE_LOG_DIR" 2>/dev/null | wc -l)
  
  echo "Found $error_count ERROR entries in Claude Desktop logs"
  if [ $error_count -gt 0 ]; then
    echo -e "${COLOR_YELLOW}Most recent errors:${COLOR_RESET}"
    grep -r "ERROR" "$CLAUDE_LOG_DIR" 2>/dev/null | tail -10
  fi
  
  # Look for specific MCP server errors
  echo -e "${COLOR_GREEN}Checking for specific MCP server errors:${COLOR_RESET}"
  grep -r "prompt-manager-py" "$CLAUDE_LOG_DIR" 2>/dev/null | grep "ERROR" || echo "No prompt-manager-py errors"
  grep -r "prompts-sse" "$CLAUDE_LOG_DIR" 2>/dev/null | grep "ERROR" || echo "No prompts-sse errors"
  grep -r "prompts-stdio" "$CLAUDE_LOG_DIR" 2>/dev/null | grep "ERROR" || echo "No prompts-stdio errors"
  grep -r "db" "$CLAUDE_LOG_DIR" 2>/dev/null | grep "ERROR" || echo "No db errors"
  grep -r "project-orchestrator" "$CLAUDE_LOG_DIR" 2>/dev/null | grep "ERROR" || echo "No project-orchestrator errors"
  
  return 0
}

# Function to run basic MCP server tests
run_basic_tests() {
  echo -e "${COLOR_GREEN}Running basic MCP server tests...${COLOR_RESET}"
  
  # Check if Node.js and npm are installed
  if ! command -v npm &> /dev/null; then
    echo -e "${COLOR_RED}Error: npm not found. Please install Node.js${COLOR_RESET}"
    exit 1
  fi
  
  # Build the container
  echo -e "${COLOR_GREEN}Building container image...${COLOR_RESET}"
  $CONTAINER_ENGINE build -t mcp-project-orchestrator:latest -f "$PROJECT_DIR/Containerfile" "$PROJECT_DIR"
  
  # Run the container with volume mounting
  echo -e "${COLOR_GREEN}Starting MCP server with volume mounting...${COLOR_RESET}"
  
  VOLUME_OPTION=""
  if [ "$CONTAINER_ENGINE" = "podman" ]; then
    VOLUME_OPTION=":Z"
    IMAGE_NAME="localhost/mcp-project-orchestrator:latest"
  else
    IMAGE_NAME="mcp-project-orchestrator:latest"
  fi
  
  $CONTAINER_ENGINE run -d --rm -p 8080:8080 \
    -v "$PROJECT_DIR:/app$VOLUME_OPTION" \
    --workdir /app \
    --entrypoint python \
    --name mcp-server \
    $IMAGE_NAME \
    -m mcp_project_orchestrator.fastmcp
  
  # Wait for server to start
  echo "Waiting for server to start..."
  sleep 5
  
  # Verify the server is running
  if ! $CONTAINER_ENGINE ps | grep -q mcp-server; then
    echo -e "${COLOR_RED}Error: MCP server failed to start${COLOR_RESET}"
    $CONTAINER_ENGINE logs mcp-server
    exit 1
  fi
  
  # Install MCP Inspector if needed
  echo -e "${COLOR_GREEN}Setting up MCP Inspector...${COLOR_RESET}"
  npm list -g @modelcontextprotocol/inspector &>/dev/null || npm install -g @modelcontextprotocol/inspector
  
  # Run basic test
  echo -e "${COLOR_GREEN}Running basic connectivity test...${COLOR_RESET}"
  npx @modelcontextprotocol/inspector http://localhost:8080 || { 
    echo -e "${COLOR_RED}Basic test failed${COLOR_RESET}"; 
    $CONTAINER_ENGINE stop mcp-server; 
    exit 1; 
  }
  
  # Run validation
  echo -e "${COLOR_GREEN}Running validation test...${COLOR_RESET}"
  npx @modelcontextprotocol/inspector http://localhost:8080 --validate || { 
    echo -e "${COLOR_RED}Validation test failed${COLOR_RESET}"; 
    $CONTAINER_ENGINE stop mcp-server; 
    exit 1; 
  }
  
  # Run interactive test if requested
  if [ "$INTERACTIVE" = true ]; then
    echo -e "${COLOR_GREEN}Running interactive test...${COLOR_RESET}"
    npx @modelcontextprotocol/inspector http://localhost:8080 --interactive
  fi
  
  # Stop the container
  echo -e "${COLOR_GREEN}Tests completed successfully. Stopping container...${COLOR_RESET}"
  $CONTAINER_ENGINE stop mcp-server
  
  echo -e "${COLOR_GREEN}All basic tests passed!${COLOR_RESET}"
}

# Function to run Claude Desktop integration tests
run_claude_desktop_tests() {
  echo -e "${COLOR_GREEN}Running Claude Desktop integration tests...${COLOR_RESET}"
  
  # Kill Claude Desktop if running
  echo "Killing Claude Desktop if running..."
  pkill -f "Claude Desktop" || true
  sleep 3  # Wait for Claude Desktop to fully terminate
  
  # Delete old logs
  echo "Cleaning up old Claude Desktop logs..."
  mkdir -p "$CLAUDE_LOG_DIR"
  rm -rf "$CLAUDE_LOG_DIR"/*
  
  # Initialize PostgreSQL if not skipped
  if [ "$SKIP_DB_INIT" = false ]; then
    initialize_postgres
  fi
  
  # Create a sample prompt template if directory is empty
  if [ ! "$(ls -A $MCP_DATA_DIR/prompts)" ]; then
    echo "Adding a sample prompt template..."
    mkdir -p "$MCP_DATA_DIR/prompts"
    cat > "$MCP_DATA_DIR/prompts/sample-template.json" << EOF
{
  "id": "sample-template",
  "name": "Sample Template",
  "description": "A sample prompt template",
  "content": "This is a sample template with a {{variable}}",
  "isTemplate": true,
  "variables": ["variable"],
  "tags": ["sample"],
  "createdAt": "$(date -Iseconds)",
  "updatedAt": "$(date -Iseconds)",
  "version": 1
}
EOF
  fi
  
  # Start prompt-manager-py container if available
  echo "Checking for prompt-manager image..."
  if $CONTAINER_ENGINE images | grep -q "prompt-manager"; then
    echo "Starting prompt-manager-py container..."
    $CONTAINER_ENGINE run -d --restart=on-failure:5 --network=host \
      -v "$MCP_DATA_DIR/prompts:/data/prompts" \
      --name mcp-prompt-manager-py \
      -e MCP_PROMPT_MANAGER_NAME=prompt-manager-py \
      -e MCP_PROMPT_MANAGER_LOG_LEVEL=debug \
      -e MCP_PROMPT_MANAGER_TEMPLATE_DIR=/data/prompts/ \
      -e MCP_PROMPT_MANAGER_PERSISTENCE=true \
      -e MCP_PROMPT_MANAGER_PERSISTENCE_FILE=/data/prompts/prompt-templates.json \
      -e PYTHONPATH=. \
      -e MCP_PROMPT_MANAGER_STANDALONE=true \
      prompt-manager:latest --storage-dir /data/prompts --standalone
  else
    echo -e "${COLOR_YELLOW}Warning: prompt-manager image not found. Skipping prompt-manager container.${COLOR_RESET}"
  fi
  
  # Start prompts-sse container if available
  echo "Checking for mcp-prompts image..."
  if $CONTAINER_ENGINE images | grep -q "sparesparrow/mcp-prompts" || $CONTAINER_ENGINE images | grep -q "mcp-prompts"; then
    echo "Starting prompts-sse container..."
    $CONTAINER_ENGINE run -d --restart=on-failure:5 --network=host \
      -v "$MCP_DATA_DIR/prompts:/app/prompts" \
      -v "$MCP_DATA_DIR/backups:/app/backups" \
      --name mcp-prompts-sse \
      -e STORAGE_TYPE=postgres \
      -e PROMPTS_DIR=/app/prompts \
      -e BACKUPS_DIR=/app/backups \
      -e HTTP_SERVER=true \
      -e PORT=3003 \
      -e HOST=0.0.0.0 \
      -e ENABLE_SSE=true \
      -e SSE_PORT=3003 \
      -e SSE_PATH=/sse \
      -e CORS_ORIGIN="*" \
      -e DEBUG="mcp:*" \
      -e POSTGRES_HOST=localhost \
      -e POSTGRES_PORT=5432 \
      -e POSTGRES_DATABASE=prompts \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=postgres \
      sparesparrow/mcp-prompts:latest --sse --port=3003 --path=/sse
  fi
  
  # Check if Claude Desktop launch script is available
  if [ ! -f "$CLAUDE_DESKTOP_BIN" ]; then
    echo -e "${COLOR_YELLOW}Warning: Claude Desktop binary not found at $CLAUDE_DESKTOP_BIN"
    echo "Please provide the path to the Claude Desktop launch script:${COLOR_RESET}"
    read -p "Claude Desktop path (leave empty to skip launch): " CLAUDE_PATH
    
    if [ -n "$CLAUDE_PATH" ]; then
      CLAUDE_DESKTOP_BIN="$CLAUDE_PATH"
    else
      echo -e "${COLOR_YELLOW}Skipping Claude Desktop launch${COLOR_RESET}"
      CLAUDE_DESKTOP_BIN=""
    fi
  fi
  
  # Launch Claude Desktop if binary is available
  if [ -n "$CLAUDE_DESKTOP_BIN" ]; then
    echo "Launching Claude Desktop..."
    "$CLAUDE_DESKTOP_BIN" &
    
    echo "Waiting for Claude Desktop to initialize (60 seconds)..."
    sleep 60
    
    echo "Stopping Claude Desktop..."
    pkill -f "Claude Desktop" || true
    sleep 5
  fi
  
  # Check logs for errors
  check_claude_logs
  
  # Check if all containers are running
  echo -e "${COLOR_GREEN}Checking containers status...${COLOR_RESET}"
  check_container_running "mcp-postgres-db-container" || echo -e "${COLOR_YELLOW}PostgreSQL container not running${COLOR_RESET}"
  check_container_running "pgai-vectorizer-worker" || echo -e "${COLOR_YELLOW}Vectorizer worker not running (optional)${COLOR_RESET}"
  check_container_running "mcp-postgres-server" || echo -e "${COLOR_YELLOW}Postgres server not running${COLOR_RESET}"
  check_container_running "mcp-prompt-manager-py" || echo -e "${COLOR_YELLOW}Prompt manager not running${COLOR_RESET}"
  check_container_running "mcp-prompts-sse" || echo -e "${COLOR_YELLOW}Prompts SSE not running${COLOR_RESET}"
  
  echo -e "${COLOR_GREEN}Claude Desktop tests completed!${COLOR_RESET}"
}

# Main execution
echo -e "${COLOR_GREEN}=== MCP Project Orchestrator Testing Script ===${COLOR_RESET}"
echo "Using container engine: $CONTAINER_ENGINE"

# Clean up existing containers
cleanup_containers

# Initialize PostgreSQL if needed (for basic tests)
if [ "$TEST_TYPE" = "basic" ] && [ "$SKIP_DB_INIT" = false ]; then
  initialize_postgres
fi

# Run selected tests
case "$TEST_TYPE" in
  "basic")
    run_basic_tests
    ;;
  "claude-desktop")
    run_claude_desktop_tests
    ;;
  *)
    echo -e "${COLOR_RED}Invalid test type: $TEST_TYPE${COLOR_RESET}"
    exit 1
    ;;
esac

echo -e "${COLOR_GREEN}All tests completed successfully!${COLOR_RESET}" 