#!/bin/bash
set -e

echo "==============================="
echo "PostgreSQL Initialization Script"
echo "==============================="

# Function to check if container is running
check_container_running() {
  local container_name="$1"
  if docker ps --filter "name=$container_name" --format "{{.Names}}" | grep -q "$container_name"; then
    return 0  # Container is running
  else
    return 1  # Container is not running
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

# Create necessary directories
echo "Creating directories..."
mkdir -p /home/sparrow/mcp/data/postgres/data
mkdir -p /home/sparrow/mcp/data/prompts
mkdir -p /home/sparrow/mcp/data/backups

# Stop and remove existing containers if they exist
echo "Cleaning up existing containers..."
docker stop mcp-postgres-db-container pgai-vectorizer-worker mcp-postgres-server mcp-prompt-manager mcp-prompts-sse 2>/dev/null || true
docker rm mcp-postgres-db-container pgai-vectorizer-worker mcp-postgres-server mcp-prompt-manager mcp-prompts-sse 2>/dev/null || true

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

# Check if PostgreSQL container is running
if ! check_container_running "mcp-postgres-db-container"; then
  echo "Error: Failed to start PostgreSQL container"
  exit 1
fi

# Wait for PostgreSQL to be ready
if ! wait_for_postgres; then
  echo "Error: PostgreSQL failed to initialize properly"
  docker logs mcp-postgres-db-container
  exit 1
fi

# Create pgai extension and schema
echo "Creating pgai extension and schema..."
docker exec mcp-postgres-db-container psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS ai CASCADE;" || {
  echo "Warning: Failed to create ai extension, it may not be installed. Continuing..."
}

docker exec mcp-postgres-db-container psql -U postgres -c "CREATE SCHEMA IF NOT EXISTS pgai;" || {
  echo "Warning: Failed to create pgai schema, continuing..."
}

# Create prompts database
echo "Creating prompts database..."
docker exec mcp-postgres-db-container psql -U postgres -c "CREATE DATABASE prompts WITH OWNER postgres;" || echo "Info: prompts database already exists or could not be created"

# Check for vectorizer worker image
if docker images | grep -q "timescale/pgai-vectorizer-worker"; then
  echo "Starting pgai-vectorizer-worker container..."
  docker run -d --restart=on-failure:5 \
    --network=mcp-network \
    --network-alias=vectorizer-worker \
    -e PGAI_VECTORIZER_WORKER_DB_URL="postgresql://postgres:postgres@postgres:5432/postgres" \
    -e PGAI_VECTORIZER_WORKER_POLL_INTERVAL="5s" \
    --name pgai-vectorizer-worker \
    timescale/pgai-vectorizer-worker:latest
  
  # Check if pgai-vectorizer-worker container is running
  if ! check_container_running "pgai-vectorizer-worker"; then
    echo "Warning: Failed to start pgai-vectorizer-worker container"
  fi
else
  echo "Warning: timescale/pgai-vectorizer-worker image not found. You can pull it with: docker pull timescale/pgai-vectorizer-worker:latest"
fi

# Start postgres-server to serve connections to PostgreSQL
echo "Starting postgres-server container..."
docker run -d --restart=on-failure:5 \
  --network=mcp-network \
  --network-alias=mcp-postgres-server \
  -p 5433:5432 \
  -e POSTGRES_CONNECTION_STRING="postgresql://postgres:postgres@postgres:5432/postgres" \
  --name mcp-postgres-server \
  mcp/postgres:latest

# Check if postgres-server container is running
if ! check_container_running "mcp-postgres-server"; then
  echo "Error: Failed to start postgres-server container"
  exit 1
fi

# Verify pgai installation
echo "Verifying database connection..."
if docker exec mcp-postgres-db-container psql -U postgres -c "SELECT version();" | grep -q "PostgreSQL"; then
  echo "✅ PostgreSQL connection successful"
else
  echo "❌ PostgreSQL connection failed"
  exit 1
fi

echo "==============================="
echo "PostgreSQL initialized successfully!"
echo "PostgreSQL running on: localhost:5432"
echo "TimescaleDB version: $(docker exec mcp-postgres-db-container psql -U postgres -c "SELECT extversion FROM pg_extension WHERE extname='timescaledb';" -t)"
echo "pgai extension: $(docker exec mcp-postgres-db-container psql -U postgres -c "SELECT extversion FROM pg_extension WHERE extname='ai';" -t || echo "Not installed")"
echo "Prompts directory: /home/sparrow/mcp/data/prompts/"
echo "==============================="
echo "To create a vectorizer and use pgai, refer to: https://github.com/timescale/pgai/blob/main/docs/vectorizer/quick-start.md"
echo "===============================" 