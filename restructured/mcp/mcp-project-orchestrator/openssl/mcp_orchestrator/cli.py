"""
Command-line interface for MCP Project Orchestrator.

This module provides CLI commands for deploying and managing Cursor
configuration, similar to Conan's CLI interface.
"""

import click
from pathlib import Path
from typing import List, Optional

from .cursor_deployer import CursorConfigDeployer
from .env_config import get_environment_config


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """MCP AI Orchestrator for OpenSSL - Cursor configuration management."""
    pass


@cli.command()
@click.option('--repo-root', type=click.Path(exists=True), default='.',
              help='Path to repository root')
@click.option('--force', is_flag=True, 
              help='Overwrite existing .cursor/ configuration')
@click.option('--custom-rules', multiple=True, type=click.Path(exists=True),
              help='Path to custom rule files to import')
@click.option('--opt-out', is_flag=True,
              help='Skip Cursor configuration deployment (developer opt-out)')
@click.option('--dry-run', is_flag=True,
              help='Show what would be deployed without making changes')
@click.option('--check-env', is_flag=True,
              help='Check environment variables and exit')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed information')
def setup_cursor(repo_root: str, force: bool, custom_rules: tuple, 
                opt_out: bool, dry_run: bool, check_env: bool, verbose: bool):
    """Deploy Cursor AI configuration to repository (like Conan profile deployment)."""
    
    # Get environment configuration
    env_config = get_environment_config()
    
    # Check environment variables
    is_valid, missing_vars = env_config.validate_required("openssl")
    if not is_valid:
        click.echo("❌ Environment validation failed:")
        for error in env_config.get_validation_errors("openssl"):
            click.echo(f"   {error}")
        return 1
    
    if check_env:
        env_config.print_status("openssl", verbose)
        return 0
    
    # Show warnings for missing optional variables
    warnings = env_config.get_warnings("openssl")
    if warnings and verbose:
        for warning in warnings:
            click.echo(f"⚠️  {warning}")
    
    repo_path = Path(repo_root).resolve()
    
    # Find package root (mcp-project-orchestrator/openssl)
    package_path = Path(__file__).parent.parent
    
    deployer = CursorConfigDeployer(repo_path, package_path)
    
    if dry_run:
        deployer.dry_run()
        return
    
    custom_rules_list = [Path(p) for p in custom_rules] if custom_rules else None
    
    deployer.deploy(
        force=force,
        custom_rules=custom_rules_list,
        opt_out=opt_out
    )


@cli.command()
@click.option('--repo-root', type=click.Path(exists=True), default='.')
def show_cursor_config(repo_root: str):
    """Show current Cursor configuration status."""
    repo_path = Path(repo_root).resolve()
    package_path = Path(__file__).parent.parent
    
    deployer = CursorConfigDeployer(repo_path, package_path)
    deployer.show_status()


@cli.command()
@click.option('--repo-root', type=click.Path(exists=True), default='.')
def detect_platform(repo_root: str):
    """Detect and display platform information."""
    repo_path = Path(repo_root).resolve()
    package_path = Path(__file__).parent.parent
    
    deployer = CursorConfigDeployer(repo_path, package_path)
    platform_info = deployer.detect_platform()
    
    print("🔍 Platform Detection Results:")
    print(f"   OS: {platform_info['os']} {platform_info['os_version']}")
    print(f"   Architecture: {platform_info['architecture']}")
    print(f"   Python: {platform_info['python_version']} ({platform_info['python_implementation']})")
    print(f"   User: {platform_info['user']}")
    print(f"   Home: {platform_info['home']}")
    print(f"   Shell: {platform_info['shell']}")
    print(f"   CI Environment: {platform_info['is_ci']}")
    if platform_info['is_ci']:
        print(f"   CI Provider: ", end="")
        if platform_info['is_github_actions']:
            print("GitHub Actions")
        elif platform_info['is_gitlab_ci']:
            print("GitLab CI")
        elif platform_info['is_jenkins']:
            print("Jenkins")
        else:
            print("Unknown")
    
    print(f"   Development Tools:")
    print(f"     Git: {'✅' if platform_info['has_git'] else '❌'}")
    print(f"     Conan: {'✅' if platform_info['has_conan'] else '❌'}")
    print(f"     Cursor: {'✅' if platform_info['has_cursor'] else '❌'}")
    
    print(f"   Virtual Environment: {'✅' if platform_info['in_venv'] else '❌'}")
    print(f"   Timestamp: {platform_info['timestamp']}")


@cli.command()
@click.option('--repo-root', type=click.Path(exists=True), default='.')
@click.option('--output', type=click.Path(), help='Output file for configuration dump')
def export_config(repo_root: str, output: Optional[str]):
    """Export current Cursor configuration for backup or sharing."""
    repo_path = Path(repo_root).resolve()
    package_path = Path(__file__).parent.parent
    
    deployer = CursorConfigDeployer(repo_path, package_path)
    
    if not deployer.cursor_dir.exists():
        click.echo("❌ No .cursor/ configuration found to export")
        return
    
    # Create export package
    import shutil
    import tempfile
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_name = f"cursor-config-export-{timestamp}"
    
    if output:
        export_path = Path(output)
    else:
        export_path = Path.cwd() / export_name
    
    # Copy .cursor directory
    if export_path.exists():
        click.echo(f"❌ Export path already exists: {export_path}")
        return
    
    shutil.copytree(deployer.cursor_dir, export_path)
    
    # Create metadata file
    platform_info = deployer.detect_platform()
    metadata = {
        "exported_at": platform_info['timestamp'],
        "platform": platform_info['os'],
        "user": platform_info['user'],
        "version": "0.1.0"
    }
    
    metadata_file = export_path / "export-metadata.json"
    import json
    metadata_file.write_text(json.dumps(metadata, indent=2))
    
    click.echo(f"✅ Configuration exported to: {export_path}")
    click.echo(f"   Rules: {len(deployer.cursor_config.get_existing_rules())} files")
    click.echo(f"   Prompts: {len(deployer.cursor_config.get_existing_prompts())} files")
    click.echo(f"   MCP config: {'✅' if deployer.cursor_config.has_mcp_config() else '❌'}")


if __name__ == '__main__':
    cli()