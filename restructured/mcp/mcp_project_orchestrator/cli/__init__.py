"""Command-line interface for the MCP Project Orchestrator.

Provides an executable entrypoint that launches the MCP server.
"""

from typing import NoReturn


def main() -> NoReturn:
    """Entry point that delegates to the fast MCP server main.

    This function serves as the console script target defined in
    `pyproject.toml` under the `project.scripts` table. It simply calls
    the orchestrator's primary server entrypoint.
    """
    from ..fastmcp import main as _fastmcp_main

    _fastmcp_main()
