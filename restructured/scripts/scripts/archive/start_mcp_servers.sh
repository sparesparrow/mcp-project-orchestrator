#!/bin/bash
set -e

echo "Starting Claude Desktop MCP servers"

# Create necessary directories
mkdir -p /home/sparrow/mcp/data/postgres/data
mkdir -p /home/sparrow/mcp/data/prompts
mkdir -p /home/sparrow/mcp/data/backups

# Function to check if container is running
check_container_running() {
  local container_name="$1"
  if docker ps --filter "name=$container_name" --format "{{.Names}}" | grep -q "$container_name"; then
    echo "✅ Container '$container_name' is running"
    return 0
  else
    echo "❌ Container '$container_name' is NOT running"
    return 1
  fi
}

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
  local max_attempts=30
  local attempt=1
  
  echo "Waiting for PostgreSQL to be ready..."
  while [ $attempt -le $max_attempts ]; do
    if docker exec mcp-postgres-db-container pg_isready -h localhost -U postgres &> /dev/null; then
      echo "PostgreSQL is ready!"
      return 0
    fi
    echo "Attempt $attempt/$max_attempts: PostgreSQL not ready yet, waiting..."
    sleep 2
    ((attempt++))
  done
  
  echo "Error: PostgreSQL did not become ready after $max_attempts attempts"
  return 1
}

# Stop existing containers
echo "Stopping existing containers..."
docker stop mcp-postgres-db-container pgai-vectorizer-worker mcp-prompt-manager mcp-prompts-sse mcp-prompts-stdio mcp-postgres-server 2>/dev/null || true
docker rm mcp-postgres-db-container pgai-vectorizer-worker mcp-prompt-manager mcp-prompts-sse mcp-prompts-stdio mcp-postgres-server 2>/dev/null || true

# Create mcp-network if it doesn't exist
if ! docker network inspect mcp-network &>/dev/null; then
  echo "Creating mcp-network..."
  docker network create mcp-network
fi

# Start PostgreSQL with TimescaleDB
echo "Starting PostgreSQL container with TimescaleDB..."
docker run -d --restart=on-failure:5 \
  --network=mcp-network \
  --network-alias=postgres \
  -p 5432:5432 \
  -v /home/sparrow/mcp/data/postgres/data:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=postgres \
  --name mcp-postgres-db-container \
  timescale/timescaledb-ha:pg17-latest

# Wait for PostgreSQL to be ready
wait_for_postgres

# Create pgai extension and schema
echo "Creating pgai extension and schema..."
docker exec mcp-postgres-db-container psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS ai CASCADE;" || echo "Info: ai extension not available"
docker exec mcp-postgres-db-container psql -U postgres -c "CREATE SCHEMA IF NOT EXISTS pgai;" || echo "Info: Could not create pgai schema"

# Create prompts database
echo "Creating prompts database..."
docker exec mcp-postgres-db-container psql -U postgres -c "CREATE DATABASE prompts WITH OWNER postgres;" || echo "Info: prompts database already exists or could not be created"

# Check for vectorizer worker image and start it if available
if docker images | grep -q "timescale/pgai-vectorizer-worker"; then
  echo "Starting pgai-vectorizer-worker container..."
  docker run -d --restart=on-failure:5 \
    --network=mcp-network \
    --network-alias=vectorizer-worker \
    -e PGAI_VECTORIZER_WORKER_DB_URL="postgresql://postgres:postgres@postgres:5432/postgres" \
    -e PGAI_VECTORIZER_WORKER_POLL_INTERVAL="5s" \
    --name pgai-vectorizer-worker \
    timescale/pgai-vectorizer-worker:latest
else
  echo "Warning: timescale/pgai-vectorizer-worker image not found. You can pull it with: docker pull timescale/pgai-vectorizer-worker:latest"
fi

# Start postgres-server container with the connection string
echo "Starting postgres-server container..."
docker run -d --restart=on-failure:5 \
  -i \
  --network=mcp-network \
  --network-alias=mcp-postgres-server \
  -p 5433:5432 \
  --name mcp-postgres-server \
  -e POSTGRES_CONNECTION_STRING="postgresql://postgres:postgres@postgres:5432/postgres" \
  mcp/postgres:latest \
  "postgresql://postgres:postgres@postgres:5432/postgres"

# Create a sample prompt template if directory is empty
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

# Create a minimal prompt-manager server in Node.js
if [ ! -f "/home/sparrow/mcp/standalone-prompt-manager.js" ]; then
  echo "Creating a standalone prompt manager script..."
  cat > /home/sparrow/mcp/standalone-prompt-manager.js << EOF
// Minimal prompt manager server in Node.js
const fs = require('fs');
const path = require('path');
const http = require('http');

const STORAGE_DIR = process.argv[2] || '/data/prompts';
const PORT = 3004;

let templates = [];
const templatesFile = path.join(STORAGE_DIR, 'prompt-templates.json');

// Load templates if file exists
try {
  if (fs.existsSync(templatesFile)) {
    templates = JSON.parse(fs.readFileSync(templatesFile, 'utf8'));
    console.log(\`Loaded \${templates.length} templates from \${templatesFile}\`);
  } else {
    console.log(\`No templates file found at \${templatesFile}, starting with empty list\`);
    
    // Look for template files in the directory
    const files = fs.readdirSync(STORAGE_DIR).filter(f => f.endsWith('.json') && f !== 'prompt-templates.json');
    for (const file of files) {
      try {
        const template = JSON.parse(fs.readFileSync(path.join(STORAGE_DIR, file), 'utf8'));
        templates.push(template);
        console.log(\`Loaded template from \${file}\`);
      } catch (err) {
        console.error(\`Error loading template \${file}: \${err.message}\`);
      }
    }
    
    if (templates.length > 0) {
      fs.writeFileSync(templatesFile, JSON.stringify(templates, null, 2));
      console.log(\`Saved \${templates.length} templates to \${templatesFile}\`);
    }
  }
} catch (err) {
  console.error(\`Error loading templates: \${err.message}\`);
}

// Create HTTP server for basic MCP protocol
const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  
  const chunks = [];
  req.on('data', chunk => chunks.push(chunk));
  
  req.on('end', () => {
    if (req.url === '/health') {
      return res.end(JSON.stringify({ status: 'ok' }));
    }
    
    let body;
    try {
      body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : {};
    } catch (err) {
      res.statusCode = 400;
      return res.end(JSON.stringify({ error: 'Invalid JSON' }));
    }
    
    // MCP request format
    if (body.jsonrpc === '2.0') {
      const { id, method, params } = body;
      
      if (method === 'get_templates') {
        return res.end(JSON.stringify({
          jsonrpc: '2.0',
          id,
          result: templates
        }));
      } else if (method === 'get_template' && params?.id) {
        const template = templates.find(t => t.id === params.id);
        
        if (!template) {
          return res.end(JSON.stringify({
            jsonrpc: '2.0',
            id,
            error: { code: 404, message: 'Template not found' }
          }));
        }
        
        return res.end(JSON.stringify({
          jsonrpc: '2.0',
          id,
          result: template
        }));
      }
      
      return res.end(JSON.stringify({
        jsonrpc: '2.0',
        id,
        error: { code: 501, message: 'Method not implemented' }
      }));
    }
    
    res.statusCode = 400;
    res.end(JSON.stringify({ error: 'Invalid request format' }));
  });
});

server.listen(PORT, () => {
  console.log(\`Standalone prompt-manager listening on port \${PORT}\`);
  console.log(\`Using storage directory: \${STORAGE_DIR}\`);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down server...');
  server.close(() => {
    console.log('Server shut down.');
    process.exit(0);
  });
});
EOF
fi

# Start prompt-manager using the Node.js implementation
echo "Starting prompt-manager using Node.js implementation..."

# Run the Node.js prompt manager container
docker run -d --restart=on-failure:5 \
  -i \
  --network=mcp-network \
  --network-alias=prompt-manager \
  -p 3004:3004 \
  -v /home/sparrow/mcp/data/prompts:/data/prompts \
  -v /home/sparrow/mcp/standalone-prompt-manager.js:/app/server.js \
  --name mcp-prompt-manager \
  -e PORT=3004 \
  node:18-alpine \
  node /app/server.js /data/prompts

# Start prompts-sse for Claude Desktop integration
echo "Starting prompts-sse for Claude Desktop integration..."
docker run -d --restart=on-failure:5 \
  -i \
  --network=mcp-network \
  --network-alias=prompts-sse \
  -p 3003:3003 \
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
  -e CORS_ORIGIN=* \
  -e DEBUG=mcp:* \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DATABASE=prompts \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  sparesparrow/mcp-prompts:latest \
  --sse \
  --port=3003 \
  --path=/sse
  
# Wait a moment for services to start
sleep 5

# Verify all containers are running
echo "Verifying containers are running..."
check_container_running "mcp-postgres-db-container"
check_container_running "pgai-vectorizer-worker" || echo "Note: pgai-vectorizer-worker is optional"
check_container_running "mcp-postgres-server"
check_container_running "mcp-prompt-manager"
check_container_running "mcp-prompts-sse"

# Show running containers
echo "Currently running containers:"
docker ps

echo "======================================================================================"
echo "MCP servers are ready. You can now start Claude Desktop."
echo "Recommended environment variables: MCP_DEFAULT_TIMEOUT=180000 DEBUG=mcp:*"
echo "======================================================================================"
echo "pgai is available in PostgreSQL at: postgresql://postgres:postgres@localhost:5432/postgres"
echo "To use vectorizers, see documentation at: https://github.com/timescale/pgai/blob/main/docs/vectorizer/quick-start.md"
echo "======================================================================================" 