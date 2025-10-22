"""Main CLI entry point for MCP Project Orchestrator."""
import click
from .commands.openssl_cli import create_openssl_project, deploy_cursor

@click.group()
def cli():
    """MCP Project Orchestrator CLI"""
    pass

# Add OpenSSL commands
cli.add_command(create_openssl_project)
cli.add_command(deploy_cursor)

def main():
    """Entry point"""
    cli()
