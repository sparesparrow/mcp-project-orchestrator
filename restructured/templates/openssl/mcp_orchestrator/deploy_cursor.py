"""
Deploy Cursor configuration for specific project types.

This module provides a specialized CLI entrypoint for deploying
Cursor configuration with project-type-specific presets.
"""

import click
import os
from pathlib import Path
from typing import Optional, Dict, Any

from .cursor_deployer import CursorConfigDeployer
from .platform_detector import PlatformDetector


class ProjectTypeConfig:
    """Configuration for different project types."""
    
    CONFIGS = {
        "openssl": {
            "name": "OpenSSL",
            "description": "OpenSSL cryptographic library development",
            "templates_dir": "cursor-rules",
            "output_paths": {
                "rules": ".cursor/rules",
                "prompts": ".cursor/prompts", 
                "mcp_config": ".cursor/mcp.json",
                "gitignore": ".cursor/.gitignore"
            },
            "required_env_vars": [
                "CONAN_USER_HOME",
                "OPENSSL_ROOT_DIR"
            ],
            "optional_env_vars": [
                "CLOUDSMITH_API_KEY",
                "CONAN_REPOSITORY_NAME",
                "GITHUB_TOKEN"
            ],
            "mcp_servers": [
                "openssl-context",
                "build-intelligence", 
                "fips-compliance",
                "security-scanner"
            ]
        },
        "generic": {
            "name": "Generic",
            "description": "Generic C++ project development",
            "templates_dir": "cursor-rules",
            "output_paths": {
                "rules": ".cursor/rules",
                "prompts": ".cursor/prompts",
                "mcp_config": ".cursor/mcp.json", 
                "gitignore": ".cursor/.gitignore"
            },
            "required_env_vars": [],
            "optional_env_vars": [
                "CONAN_USER_HOME",
                "GITHUB_TOKEN"
            ],
            "mcp_servers": [
                "build-intelligence",
                "workflow-orchestrator"
            ]
        }
    }
    
    @classmethod
    def get_config(cls, project_type: str) -> Dict[str, Any]:
        """Get configuration for a project type."""
        if project_type not in cls.CONFIGS:
            raise ValueError(f"Unknown project type: {project_type}. Available: {', '.join(cls.CONFIGS.keys())}")
        return cls.CONFIGS[project_type]
    
    @classmethod
    def list_types(cls) -> list:
        """List available project types."""
        return list(cls.CONFIGS.keys())


def check_environment_variables(project_type: str, verbose: bool = False) -> tuple[bool, list[str]]:
    """
    Check environment variables for a project type.
    
    Args:
        project_type: Type of project
        verbose: Show detailed information
        
    Returns:
        Tuple of (all_required_present, missing_vars)
    """
    config = ProjectTypeConfig.get_config(project_type)
    missing_vars = []
    
    # Check required environment variables
    for var in config["required_env_vars"]:
        if not os.getenv(var):
            missing_vars.append(var)
    
    # Check optional environment variables
    optional_missing = []
    for var in config["optional_env_vars"]:
        if not os.getenv(var):
            optional_missing.append(var)
    
    if verbose:
        click.echo(f"Environment variables for {project_type} project:")
        click.echo(f"  Required: {', '.join(config['required_env_vars']) or 'None'}")
        click.echo(f"  Optional: {', '.join(config['optional_env_vars']) or 'None'}")
        
        if missing_vars:
            click.echo(f"  ❌ Missing required: {', '.join(missing_vars)}")
        else:
            click.echo("  ✅ All required variables present")
        
        if optional_missing:
            click.echo(f"  ⚠️  Missing optional: {', '.join(optional_missing)}")
        else:
            click.echo("  ✅ All optional variables present")
    
    return len(missing_vars) == 0, missing_vars


@click.command()
@click.option('--project-type', 
              type=click.Choice(ProjectTypeConfig.list_types()),
              default='openssl',
              help='Type of project to configure')
@click.option('--repo-root', 
              type=click.Path(exists=True), 
              default='.',
              help='Path to repository root')
@click.option('--force', 
              is_flag=True,
              help='Overwrite existing .cursor/ configuration')
@click.option('--custom-rules', 
              multiple=True, 
              type=click.Path(exists=True),
              help='Path to custom rule files to import')
@click.option('--opt-out', 
              is_flag=True,
              help='Skip Cursor configuration deployment (developer opt-out)')
@click.option('--dry-run', 
              is_flag=True,
              help='Show what would be deployed without making changes')
@click.option('--check-env', 
              is_flag=True,
              help='Check environment variables and exit')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Show detailed information')
def deploy_cursor(project_type: str, 
                 repo_root: str, 
                 force: bool, 
                 custom_rules: tuple,
                 opt_out: bool, 
                 dry_run: bool,
                 check_env: bool,
                 verbose: bool):
    """
    Deploy Cursor AI configuration for specific project types.
    
    This command provides project-type-specific configuration deployment
    with preset output paths and environment variable validation.
    """
    
    # Get project configuration
    try:
        config = ProjectTypeConfig.get_config(project_type)
    except ValueError as e:
        click.echo(f"❌ {e}")
        return 1
    
    click.echo(f"🚀 Deploying Cursor configuration for {config['name']} project")
    click.echo(f"   Description: {config['description']}")
    
    # Check environment variables
    env_valid, missing_vars = check_environment_variables(project_type, verbose)
    
    if not env_valid:
        click.echo(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        click.echo("   Please set these variables and try again.")
        return 1
    
    if check_env:
        click.echo("✅ Environment check completed")
        return 0
    
    # Show output paths
    if verbose:
        click.echo(f"   Output paths:")
        for key, path in config["output_paths"].items():
            click.echo(f"     {key}: {path}")
        
        click.echo(f"   MCP servers: {', '.join(config['mcp_servers'])}")
    
    # Deploy configuration
    repo_path = Path(repo_root).resolve()
    package_root = Path(__file__).parent.parent
    
    deployer = CursorConfigDeployer(repo_path, package_root)
    
    if dry_run:
        click.echo("🔍 Dry run mode - no files will be created")
        deployer.dry_run()
        return 0
    
    custom_rules_list = [Path(p) for p in custom_rules] if custom_rules else None
    
    try:
        deployer.deploy(
            force=force,
            custom_rules=custom_rules_list,
            opt_out=opt_out
        )
        
        # Validate deployed configuration
        if not opt_out:
            from .yaml_validator import validate_cursor_configuration
            cursor_dir = repo_path / ".cursor"
            
            if cursor_dir.exists():
                is_valid, errors = validate_cursor_configuration(cursor_dir)
                if not is_valid:
                    click.echo("⚠️  Configuration validation warnings:")
                    for error in errors:
                        click.echo(f"   {error}")
                elif verbose:
                    click.echo("✅ Configuration validation passed")
        
        click.echo(f"🎉 Cursor configuration deployed successfully for {config['name']} project!")
        return 0
        
    except Exception as e:
        click.echo(f"❌ Deployment failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


@click.group()
def cli():
    """Cursor configuration deployment for project types."""
    pass


cli.add_command(deploy_cursor)


if __name__ == '__main__':
    cli()