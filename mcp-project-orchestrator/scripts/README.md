# MCP Project Orchestrator Scripts

This directory contains scripts for setting up, configuring, and testing the MCP Project Orchestrator.

## Main Scripts

### `setup_mcp.sh`

Unified setup script that handles all aspects of setting up the MCP Project Orchestrator.

```bash
./setup_mcp.sh [options]
```

Options:
- `--python`: Setup with direct Python integration
- `--docker`: Setup with Docker integration
- `--podman`: Setup with Podman integration
- `--claude-desktop`: Setup with Claude Desktop integration
- `--db-only`: Initialize PostgreSQL database only
- `--help`: Display help message

If no options are provided, the script will prompt for the setup type.

### `test_mcp.sh`

Unified testing script for validating the MCP Project Orchestrator functionality.

```bash
./test_mcp.sh [options]
```

Options:
- `--basic`: Run basic MCP server tests
- `--claude-desktop`: Test Claude Desktop integration
- `--docker`: Use Docker for container operations (default)
- `--podman`: Use Podman for container operations
- `--interactive`: Run in interactive mode
- `--skip-db-init`: Skip database initialization
- `--help`: Display help message

If no test type is specified, the script will prompt for the type of test to run.

## Support Scripts

### `setup_claude_desktop.py`

Python script that configures Claude Desktop to use the MCP Project Orchestrator. This script is called by `setup_mcp.sh` and shouldn't be used directly unless you're customizing the setup process.

## Examples

### Basic Setup with Docker

```bash
./setup_mcp.sh --docker
```

### Test Claude Desktop Integration

```bash
./test_mcp.sh --claude-desktop
```

### Interactive Testing with Podman

```bash
./test_mcp.sh --basic --podman --interactive
```

## Database Setup

The scripts use a PostgreSQL database with TimescaleDB for storing persistent data. The database is initialized with the following:

- PostgreSQL running on port 5432
- TimescaleDB extension
- pgai extension and schema (if available)
- Prompts database for storing templates
- pgai-vectorizer-worker container (if available)

## Claude Desktop Integration

Claude Desktop integration involves:

1. Setting up the PostgreSQL database
2. Creating a Claude Desktop configuration file
3. Starting the necessary MCP servers (prompt-manager, prompts-sse, etc.)
4. Testing the integration

The integration allows Claude Desktop to use the MCP Project Orchestrator for template and project management.

## Container Support

The scripts support both Docker and Podman for containerization. All containers are created on the `mcp-network` docker network to enable communication between containers.

## Troubleshooting

If you encounter any issues:

1. Use `test_mcp.sh` to diagnose problems
2. Check container logs with `docker logs <container-name>`
3. Verify Claude Desktop logs in `~/.config/Claude/logs`
4. Ensure all required containers are running with `docker ps` 