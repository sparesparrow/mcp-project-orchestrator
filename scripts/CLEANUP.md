# Scripts to Remove After Consolidation

The following scripts have been consolidated into `setup_mcp.sh` and `test_mcp.sh` and can be safely removed:

- `init_postgres.sh`: Functionality merged into `setup_mcp.sh --db-only`
- `start_mcp_servers.sh`: Functionality merged into `setup_mcp.sh` and `test_mcp.sh`
- `test_claude_desktop.sh`: Functionality merged into `test_mcp.sh --claude-desktop`
- `init_claude_test.sh`: Functionality merged into `test_mcp.sh --claude-desktop`
- `mcp_test.sh`: Functionality merged into `test_mcp.sh --basic`
- `setup_docker_config.sh`: Functionality merged into `setup_mcp.sh --docker`
- `setup_podman_config.sh`: Functionality merged into `setup_mcp.sh --podman`
- `setup_claude.sh`: Functionality merged into `setup_mcp.sh --claude-desktop`

The following files should be kept as they are still needed:

- `setup_claude_desktop.py`: Still used by `setup_mcp.sh` for Claude Desktop configuration
- `README.md`: Updated with new information about consolidated scripts
- `INSTRUCTIONS.md`: Should be reviewed and might be merged into README.md

To remove the old scripts, run:

```bash
# Review this list before executing
cd /home/sparrow/projects/mcp-project-orchestrator/scripts
rm init_postgres.sh start_mcp_servers.sh test_claude_desktop.sh init_claude_test.sh mcp_test.sh setup_docker_config.sh setup_podman_config.sh setup_claude.sh
```

Alternatively, if you want to keep them for reference, you can move them to an archive directory:

```bash
# Create archive directory
mkdir -p /home/sparrow/projects/mcp-project-orchestrator/scripts/archive

# Move old scripts
mv init_postgres.sh start_mcp_servers.sh test_claude_desktop.sh init_claude_test.sh mcp_test.sh setup_docker_config.sh setup_podman_config.sh setup_claude.sh /home/sparrow/projects/mcp-project-orchestrator/scripts/archive/
``` 