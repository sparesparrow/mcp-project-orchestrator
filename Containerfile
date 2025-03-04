# Containerfile for mcp-project-orchestrator

FROM python:3.12-slim

WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install the package in editable mode with required flags
RUN pip install --no-cache-dir -e . --break-system-packages

# Expose port (adjust if needed, e.g., if the server listens on a specific port)
EXPOSE 8080

# Start the MCP server (adjust the command if needed)
CMD ["python", "-m", "mcp_project_orchestrator.fastmcp"] 