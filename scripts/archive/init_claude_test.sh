#!/bin/bash
set -e

echo "Starting Claude Desktop Automated Test"

# First stop and cleanup all containers
echo "Cleaning up existing containers..."
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

# Kill Claude Desktop if running
echo "Killing Claude Desktop if running..."
pkill -f "Claude Desktop" || true
sleep 3  # Give it time to fully terminate

# Delete old logs
echo "Cleaning up old Claude Desktop logs..."
rm -rf /home/sparrow/.config/Claude/logs/*
mkdir -p /home/sparrow/.config/Claude/logs

# Initialize PostgreSQL
echo "Initializing PostgreSQL..."
./init_postgres.sh

# Ensure PostgreSQL is ready
echo "Ensuring PostgreSQL is fully ready..."
for i in {1..10}; do
  if docker exec -it mcp-postgres-db-container pg_isready -U postgres > /dev/null 2>&1; then
    echo "PostgreSQL is ready!"
    break
  fi
  echo "Waiting for PostgreSQL to be ready (attempt $i/10)..."
  sleep 3
done

# Create directory for prompt-manager if it doesn't exist
echo "Creating directory structure for prompt-manager..."
mkdir -p /home/sparrow/mcp/data/prompts

# Add a sample prompt template if directory is empty
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

# Start the mcp-prompts-sse and mcp-prompts-stdio containers manually first
echo "Starting prompts-sse container..."
docker run -d --rm -i --network=host \
  -v /home/sparrow/mcp/data/prompts:/app/prompts \
  -v /home/sparrow/mcp/data/backups:/app/backups \
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
  -e POSTGRES_PASSWORD=password \
  sparesparrow/mcp-prompts:latest --sse --port=3003 --path=/sse

echo "Starting prompts-stdio container..."
docker run -d --rm -i --network=host \
  -v /home/sparrow/mcp/data/prompts:/app/prompts \
  -v /home/sparrow/mcp/data/backups:/app/backups \
  --name mcp-prompts-stdio \
  -e STORAGE_TYPE=postgres \
  -e PROMPTS_DIR=/app/prompts \
  -e BACKUPS_DIR=/app/backups \
  -e ENABLE_MCP=true \
  -e DEBUG="mcp:*" \
  -e POSTGRES_HOST=localhost \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DATABASE=prompts \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  sparesparrow/mcp-prompts:latest --stdio

echo "Starting prompt-manager-py container..."
# First check if prompt-manager image exists
if ! docker image inspect prompt-manager:latest >/dev/null 2>&1; then
  echo "Error: prompt-manager:latest image not found. Please build the image first."
  echo "Attempting to pull from Docker Hub as fallback..."
  docker pull sparesparrow/prompt-manager:latest && \
  docker tag sparesparrow/prompt-manager:latest prompt-manager:latest || \
  { echo "Failed to get prompt-manager image. Continuing without prompt-manager."; }
fi

# Now start the container with restart policy and error handling
docker run -d --restart=on-failure:5 --network=host \
  -v /home/sparrow/mcp/data/prompts:/data/prompts \
  --name mcp-prompt-manager-py \
  -e MCP_PROMPT_MANAGER_NAME=prompt-manager-py \
  -e MCP_PROMPT_MANAGER_LOG_LEVEL=debug \
  -e MCP_PROMPT_MANAGER_TEMPLATE_DIR=/data/prompts/ \
  -e MCP_PROMPT_MANAGER_PERSISTENCE=true \
  -e MCP_PROMPT_MANAGER_PERSISTENCE_FILE=/data/prompts/prompt-templates.json \
  -e PYTHONPATH=. \
  prompt-manager:latest --storage-dir /data/prompts

# Check if prompt-manager started properly
sleep 5
if ! docker ps | grep -q mcp-prompt-manager-py; then
  echo "Error: prompt-manager-py container failed to start. Checking logs:"
  docker logs mcp-prompt-manager-py || echo "Could not retrieve logs"
  
  echo "Attempting to start without depending on prompts-sse..."
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
fi

echo "Starting mcp-postgres-server..."
docker run -d --restart=on-failure:5 --network=host \
  --name mcp-postgres-server \
  -e POSTGRES_CONNECTION_STRING=postgresql://postgres:password@localhost:5432/postgres \
  mcp/postgres postgresql://postgres:password@localhost:5432/postgres

# Wait for all containers to initialize
echo "Waiting for all MCP servers to initialize..."
sleep 15

# Display running containers
echo "Currently running containers:"
docker ps

# Run Claude Desktop with increased timeouts
echo "Starting Claude Desktop..."
ADDITIONAL_ENV="MCP_DEFAULT_TIMEOUT=180000 DEBUG=mcp:*" ~/bin/run-claude.sh &
CLAUDE_PID=$!

# Longer wait time before checking
echo "Waiting for two minutes..."
sleep 120

# Kill Claude Desktop
echo "Killing Claude Desktop..."
kill $CLAUDE_PID || true
sleep 5

# Check logs and containers
echo "Checking if MCP servers are running..."
docker ps | grep -E "postgres|prompt|pgai"

echo "Checking pgai functionality..."
docker exec -it mcp-postgres-db-container psql -U postgres -c "SELECT version();"
docker exec -it mcp-postgres-db-container psql -U postgres -c "SELECT * FROM pg_extension WHERE extname = 'ai';"

echo "Checking prompt-manager functionality..."
if docker ps | grep -q mcp-prompt-manager-py; then
  echo "✅ prompt-manager-py is running"
else
  echo "❌ prompt-manager-py is NOT running. Starting it again..."
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
fi

echo "Test completed. You can now run Claude Desktop normally." 