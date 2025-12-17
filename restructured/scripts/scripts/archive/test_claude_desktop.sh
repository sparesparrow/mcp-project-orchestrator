#!/bin/bash
set -e

echo "Starting Claude Desktop MCP servers test script"

# Function to check Docker container status
check_container() {
  local container_name="$1"
  if docker ps --filter "name=$container_name" --format "{{.Names}}" | grep -q "$container_name"; then
    echo "✅ Container '$container_name' is running"
    return 0
  else
    echo "❌ Container '$container_name' is NOT running"
    return 1
  fi
}

# Function to check Claude Desktop logs
check_logs() {
  local log_dir="/home/sparrow/.config/Claude/logs"
  local error_count=$(grep -r "ERROR" "$log_dir" 2>/dev/null | wc -l)
  
  echo "Found $error_count ERROR entries in Claude Desktop logs"
  if [ $error_count -gt 0 ]; then
    echo "Most recent errors:"
    grep -r "ERROR" "$log_dir" 2>/dev/null | tail -10
  fi
  
  # Look for specific MCP server errors
  echo "Checking for specific MCP server errors:"
  grep -r "prompt-manager-py" "$log_dir" 2>/dev/null | grep "ERROR" || echo "No prompt-manager-py errors"
  grep -r "prompts-sse" "$log_dir" 2>/dev/null | grep "ERROR" || echo "No prompts-sse errors"
  grep -r "prompts-stdio" "$log_dir" 2>/dev/null | grep "ERROR" || echo "No prompts-stdio errors"
  grep -r "db" "$log_dir" 2>/dev/null | grep "ERROR" || echo "No db errors"
}

# Function to clean up existing containers
cleanup_containers() {
  echo "Cleaning up existing containers..."
  
  # List of containers to clean up
  containers=(
    "mcp-postgres-db-container"
    "pgai-vectorizer-worker"
    "mcp-prompt-manager-py"
    "mcp-prompts-sse"
    "mcp-prompts-stdio"
    "mcp-postgres-server"
  )
  
  for container in "${containers[@]}"; do
    echo "Stopping and removing container: $container"
    docker stop "$container" 2>/dev/null || true
    docker rm "$container" 2>/dev/null || true
  done
}

# Function to start prompt-manager in standalone mode
start_prompt_manager() {
  echo "Starting prompt-manager-py in standalone mode..."
  
  # First check if the container is already running
  if docker ps --filter "name=mcp-prompt-manager-py" --format "{{.Names}}" | grep -q "mcp-prompt-manager-py"; then
    echo "prompt-manager-py is already running"
    return 0
  fi
  
  # Check if prompt-manager image exists
  if ! docker image inspect prompt-manager:latest >/dev/null 2>&1; then
    echo "Error: prompt-manager:latest image not found. Please build the image first."
    echo "Attempting to pull from Docker Hub as fallback..."
    docker pull sparesparrow/prompt-manager:latest && \
    docker tag sparesparrow/prompt-manager:latest prompt-manager:latest || \
    return 1
  fi
  
  # Create directory for prompts if it doesn't exist
  mkdir -p /home/sparrow/mcp/data/prompts
  
  # Add a sample template if directory is empty
  if [ ! "$(ls -A /home/sparrow/mcp/data/prompts)" ]; then
    echo "Adding a sample prompt template..."
    cat > /home/sparrow/mcp/data/prompts/sample-template.json << EOF
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
  
  # Start the container
  docker run -d --restart=on-failure:5 --network=host \
    -v /home/sparrow/mcp/data/prompts:/data/prompts \
    --name mcp-prompt-manager-py \
    -e MCP_PROMPT_MANAGER_NAME=prompt-manager-py \
    -e MCP_PROMPT_MANAGER_LOG_LEVEL=debug \
    -e MCP_PROMPT_MANAGER_TEMPLATE_DIR=/data/prompts/ \
    -e MCP_PROMPT_MANAGER_PERSISTENCE=true \
    -e MCP_PROMPT_MANAGER_PERSISTENCE_FILE=/data/prompts/prompt-templates.json \
    -e PYTHONPATH=. \
    -e MCP_PROMPT_MANAGER_STANDALONE=true \
    prompt-manager:latest --storage-dir /data/prompts --standalone
  
  # Check if started successfully
  sleep 5
  if docker ps --filter "name=mcp-prompt-manager-py" --format "{{.Names}}" | grep -q "mcp-prompt-manager-py"; then
    echo "✅ Successfully started prompt-manager-py"
    return 0
  else
    echo "❌ Failed to start prompt-manager-py. Checking logs:"
    docker logs mcp-prompt-manager-py 2>&1 || true
    return 1
  fi
}

# Kill Claude Desktop if running
echo "Killing Claude Desktop if running..."
pkill -f "Claude Desktop" || true
sleep 3  # Wait for Claude Desktop to fully terminate

# Delete old logs
echo "Cleaning up old Claude Desktop logs..."
rm -rf /home/sparrow/.config/Claude/logs/*
mkdir -p /home/sparrow/.config/Claude/logs

# Clean up existing containers
cleanup_containers

# Initialize PostgreSQL (optional - run if needed)
echo "Do you want to initialize PostgreSQL? (y/n)"
read -r answer
if [[ "$answer" == "y" ]]; then
  ./init_postgres.sh
fi

# Start the prompt manager in standalone mode
echo "Do you want to start the prompt manager? (y/n)"
read -r start_pm
if [[ "$start_pm" == "y" ]]; then
  start_prompt_manager
fi

# List running containers before starting Claude Desktop
echo "Running containers before starting Claude Desktop:"
docker ps

# Run Claude Desktop with extended timeout
echo "Starting Claude Desktop..."
ADDITIONAL_ENV="MCP_DEFAULT_TIMEOUT=180000 DEBUG=mcp:*" ~/bin/run-claude.sh &
CLAUDE_PID=$!

# Wait for one minute
echo "Waiting for one minute..."
sleep 60

# Kill Claude Desktop
echo "Killing Claude Desktop..."
kill $CLAUDE_PID || true

# Wait for Claude Desktop to shut down
sleep 5

# Check logs
echo "Checking Claude Desktop logs..."
check_logs

# Check container status
echo "Checking container status..."
check_container "mcp-postgres-db-container"
check_container "pgai-vectorizer-worker"
check_container "mcp-prompt-manager-py"
check_container "mcp-prompts-sse"
check_container "mcp-prompts-stdio"
check_container "mcp-postgres-server"

# If prompt manager isn't running, try to start it again
if ! check_container "mcp-prompt-manager-py"; then
  echo "Attempting to restart prompt-manager-py..."
  start_prompt_manager
fi

echo "Test script completed!" 