#!/bin/bash
# Docker entrypoint for PrintCast Agent

set -e

echo "Starting PrintCast Agent services..."

# Start CUPS if available
if command -v cupsd &> /dev/null; then
    echo "Starting CUPS printing service..."
    sudo service cups start || echo "CUPS start failed (may need root)"
fi

# Start Asterisk if configured
if [ -n "$ASTERISK_ENABLED" ] && command -v asterisk &> /dev/null; then
    echo "Starting Asterisk PBX..."
    sudo asterisk -f -U asterisk -G asterisk &
    sleep 5
fi

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 3

# Check if running as MCP server or standalone
if [ "$1" = "mcp" ] || [ -z "$1" ]; then
    echo "Starting PrintCast MCP Server..."
    exec python -m mcp_server.main
else
    # Execute any other command
    exec "$@"
fi