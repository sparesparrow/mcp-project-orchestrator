#!/bin/bash
# MCP Project Orchestrator - Unified Setup Script
# Consolidates multiple setup scripts for easier management

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

# Setup type selection
SETUP_TYPE=""
CONTAINER_ENGINE="docker"  # Default to docker

# Function to display help message
display_help() {
  echo "MCP Project Orchestrator - Unified Setup Script"
  echo
  echo "Usage: $0 [options]"
  echo
  echo "Options:"
  echo "  --python           Setup with direct Python integration"
  echo "  --docker           Setup with Docker integration"
  echo "  --podman           Setup with Podman integration"
  echo "  --claude-desktop   Setup with Claude Desktop integration"
  echo "  --db-only          Initialize PostgreSQL database only"
  echo "  --help             Display this help message"
  echo
}

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      SETUP_TYPE="python"
      shift
      ;;
    --docker)
      SETUP_TYPE="docker"
      CONTAINER_ENGINE="docker"
      shift
      ;;
    --podman)
      SETUP_TYPE="docker"
      CONTAINER_ENGINE="podman"
      shift
      ;;
    --claude-desktop)
      SETUP_TYPE="claude-desktop"
      shift
      ;;
    --db-only)
      SETUP_TYPE="db-only"
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

# If no setup type specified, ask the user
if [ -z "$SETUP_TYPE" ]; then
  echo "Please select setup type:"
  echo "1) Python integration"
  echo "2) Docker integration"
  echo "3) Podman integration"
  echo "4) Claude Desktop integration"
  echo "5) Database setup only"
  echo "6) Exit"
  
  read -p "Enter your choice (1-6): " choice
  
  case "$choice" in
    1)
      SETUP_TYPE="python"
      ;;
    2)
      SETUP_TYPE="docker"
      CONTAINER_ENGINE="docker"
      ;;
    3)
      SETUP_TYPE="docker"
      CONTAINER_ENGINE="podman"
      ;;
    4)
      SETUP_TYPE="claude-desktop"
      ;;
    5)
      SETUP_TYPE="db-only"
      ;;
    6)
      echo "Exiting..."
      exit 0
      ;;
    *)
      echo -e "${COLOR_RED}Invalid choice. Exiting.${COLOR_RESET}"
      exit 1
      ;;
  esac
fi

# Create necessary directories
create_directories() {
  echo -e "${COLOR_GREEN}Creating necessary directories...${COLOR_RESET}"
  mkdir -p "$MCP_DATA_DIR/postgres/data"
  mkdir -p "$MCP_DATA_DIR/prompts"
  mkdir -p "$MCP_DATA_DIR/backups"
}

# Initialize PostgreSQL database
initialize_postgres() {
  echo -e "${COLOR_GREEN}Initializing PostgreSQL database...${COLOR_RESET}"
  
  # Stop and remove existing containers
  echo "Cleaning up existing containers..."
  $CONTAINER_ENGINE stop mcp-postgres-db-container pgai-vectorizer-worker mcp-postgres-server 2>/dev/null || true
  $CONTAINER_ENGINE rm mcp-postgres-db-container pgai-vectorizer-worker mcp-postgres-server 2>/dev/null || true

  # Create mcp-network if it doesn't exist
  if ! $CONTAINER_ENGINE network inspect mcp-network &>/dev/null; then
    echo "Creating mcp-network..."
    $CONTAINER_ENGINE network create mcp-network
  fi

  # Start PostgreSQL with TimescaleDB
  echo "Starting PostgreSQL container with TimescaleDB..."
  $CONTAINER_ENGINE run -d --restart=on-failure:5 \
    --network=mcp-network \
    --network-alias=postgres \
    -p 5432:5432 \
    -v "$MCP_DATA_DIR/postgres/data:/var/lib/postgresql/data" \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_DB=postgres \
    --name mcp-postgres-db-container \
    timescale/timescaledb-ha:pg17-latest

  # Wait for PostgreSQL to be ready
  echo "Waiting for PostgreSQL to be ready..."
  for i in {1..30}; do
    if $CONTAINER_ENGINE exec mcp-postgres-db-container pg_isready -h localhost -U postgres &> /dev/null; then
      echo "PostgreSQL is ready!"
      break
    fi
    echo "Attempt $i/30: PostgreSQL not ready yet, waiting..."
    sleep 2
    if [ $i -eq 30 ]; then
      echo -e "${COLOR_RED}Error: PostgreSQL did not become ready after 30 attempts${COLOR_RESET}"
      $CONTAINER_ENGINE logs mcp-postgres-db-container
      exit 1
    fi
  done

  # Create pgai extension and schema
  echo "Creating pgai extension and schema..."
  $CONTAINER_ENGINE exec mcp-postgres-db-container psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS ai CASCADE;" || \
    echo -e "${COLOR_YELLOW}Warning: Failed to create ai extension, it may not be installed. Continuing...${COLOR_RESET}"

  $CONTAINER_ENGINE exec mcp-postgres-db-container psql -U postgres -c "CREATE SCHEMA IF NOT EXISTS pgai;" || \
    echo -e "${COLOR_YELLOW}Warning: Failed to create pgai schema, continuing...${COLOR_RESET}"

  # Create prompts database
  echo "Creating prompts database..."
  $CONTAINER_ENGINE exec mcp-postgres-db-container psql -U postgres -c "CREATE DATABASE prompts WITH OWNER postgres;" || \
    echo "Info: prompts database already exists or could not be created"

  # Check for vectorizer worker image
  if $CONTAINER_ENGINE images | grep -q "timescale/pgai-vectorizer-worker"; then
    echo "Starting pgai-vectorizer-worker container..."
    $CONTAINER_ENGINE run -d --restart=on-failure:5 \
      --network=mcp-network \
      --network-alias=vectorizer-worker \
      -e PGAI_VECTORIZER_WORKER_DB_URL="postgresql://postgres:postgres@postgres:5432/postgres" \
      -e PGAI_VECTORIZER_WORKER_POLL_INTERVAL="5s" \
      --name pgai-vectorizer-worker \
      timescale/pgai-vectorizer-worker:latest
  else
    echo -e "${COLOR_YELLOW}Warning: timescale/pgai-vectorizer-worker image not found. You can pull it with: docker pull timescale/pgai-vectorizer-worker:latest${COLOR_RESET}"
  fi

  # Start postgres-server to serve connections to PostgreSQL
  echo "Starting postgres-server container..."
  $CONTAINER_ENGINE run -d --restart=on-failure:5 \
    --network=mcp-network \
    --network-alias=mcp-postgres-server \
    -p 5433:5432 \
    -e POSTGRES_CONNECTION_STRING="postgresql://postgres:postgres@postgres:5432/postgres" \
    --name mcp-postgres-server \
    mcp/postgres:latest

  # Verify database connection
  echo "Verifying database connection..."
  if $CONTAINER_ENGINE exec mcp-postgres-db-container psql -U postgres -c "SELECT version();" | grep -q "PostgreSQL"; then
    echo -e "${COLOR_GREEN}✅ PostgreSQL connection successful${COLOR_RESET}"
  else
    echo -e "${COLOR_RED}❌ PostgreSQL connection failed${COLOR_RESET}"
    exit 1
  fi

  echo -e "${COLOR_GREEN}PostgreSQL initialized successfully!${COLOR_RESET}"
}

# Setup Claude Desktop integration
setup_claude_desktop() {
  echo -e "${COLOR_GREEN}Setting up Claude Desktop integration...${COLOR_RESET}"
  
  # Find a suitable Python interpreter
  PYTHON=""
  if command -v python3 &> /dev/null; then
    PYTHON="python3"
  elif command -v python &> /dev/null; then
    PYTHON="python"
  elif [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
  else
    echo -e "${COLOR_RED}Error: Could not find a Python interpreter. Please install Python 3 and try again.${COLOR_RESET}"
    exit 1
  fi
  
  # Clean environment variables to avoid conflicts
  unset PYTHONHOME
  unset PYTHONPATH
  
  echo "Using Python interpreter: $PYTHON"
  
  # Run the Python setup script
  $PYTHON "$SCRIPT_DIR/setup_claude_desktop.py" --$SETUP_TYPE ${CONTAINER_ENGINE:+"--container-engine"} ${CONTAINER_ENGINE:+"$CONTAINER_ENGINE"}
}

# Setup container configuration (Docker/Podman)
setup_container_config() {
  echo -e "${COLOR_GREEN}Setting up $CONTAINER_ENGINE configuration...${COLOR_RESET}"
  
  # Determine config path based on OS
  if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
  elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32" ]]; then
    CONFIG_PATH="$APPDATA/Claude/claude_desktop_config.json"
  else
    CONFIG_PATH="$HOME/.config/Claude/claude_desktop_config.json"
  fi
  
  echo "Claude Desktop config path: $CONFIG_PATH"
  
  # Create config directory if it doesn't exist
  mkdir -p "$(dirname "$CONFIG_PATH")"
  
  # Determine volume mount option for Podman
  VOLUME_OPTION=":Z"
  if [ "$CONTAINER_ENGINE" == "docker" ]; then
    VOLUME_OPTION=""
    IMAGE_NAME="mcp-project-orchestrator:latest"
  else
    IMAGE_NAME="localhost/mcp-project-orchestrator:latest"
  fi
  
  # Create or update the configuration
  cat > "$CONFIG_PATH" << EOL
{
  "mcpServers": {
    "project-orchestrator": {
      "command": "$CONTAINER_ENGINE",
      "args": [
        "run",
        "--rm",
        "-p",
        "8080:8080",
        "-v",
        "${PROJECT_DIR}:/app${VOLUME_OPTION}",
        "--workdir",
        "/app",
        "--entrypoint",
        "python",
        "$IMAGE_NAME",
        "-m",
        "mcp_project_orchestrator.fastmcp"
      ]
    }
  }
}
EOL
  
  echo -e "${COLOR_GREEN}Configuration saved to $CONFIG_PATH${COLOR_RESET}"
  echo "Please restart Claude Desktop to apply the changes."
}

# Main execution
create_directories

case "$SETUP_TYPE" in
  "python"|"claude-desktop")
    initialize_postgres
    setup_claude_desktop
    ;;
  "docker")
    initialize_postgres
    setup_container_config
    ;;
  "db-only")
    initialize_postgres
    ;;
  *)
    echo -e "${COLOR_RED}Invalid setup type: $SETUP_TYPE${COLOR_RESET}"
    exit 1
    ;;
esac

echo -e "${COLOR_GREEN}Setup completed successfully!${COLOR_RESET}" 