# Containerfile for mcp-project-orchestrator

# Use a specific version for better reproducibility
FROM python:3.12-slim

# Create a non-root user for better security
RUN useradd -m mcp-user

# Set working directory
WORKDIR /app

# Copy only requirements first to leverage Docker caching
COPY pyproject.toml ./

# Install dependencies in a single layer
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy the rest of the application
COPY . .

# Change ownership to non-root user
RUN chown -R mcp-user:mcp-user /app

# Switch to non-root user
USER mcp-user

# Expose the MCP server port
EXPOSE 8080

# Set environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Run command with proper signal handling
CMD ["python", "-m", "mcp_project_orchestrator.fastmcp"] 