# Containerfile for mcp-project-orchestrator

# Use a specific version for better reproducibility
FROM python:3.12-slim

# Create a non-root user for better security
RUN useradd -m mcp-user

# Set working directory
WORKDIR /app

# Copy project metadata and sources
COPY pyproject.toml ./
COPY README.md LICENSE ./
COPY src ./src

# Install the application
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Change ownership to non-root user
RUN chown -R mcp-user:mcp-user /app

# Switch to non-root user
USER mcp-user

# Expose the MCP server port
EXPOSE 8080

# Set environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Run command with proper signal handling
CMD ["mcp-orchestrator"]