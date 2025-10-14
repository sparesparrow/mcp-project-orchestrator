"""OpenSSL project orchestration commands."""
import click
import os
from pathlib import Path
from typing import Optional

@click.command()
@click.option('--template', default='openssl-consumer', 
              help='Project template (openssl-consumer, openssl-fips)')
@click.option('--project-name', prompt='Project name', help='Name of the project')
@click.option('--openssl-version', default='3.4.1', help='OpenSSL version')
@click.option('--deployment-target', 
              type=click.Choice(['general', 'fips-government', 'embedded']),
              default='general', help='Deployment target')
@click.option('--enable-fips', is_flag=True, help='Enable FIPS mode')
@click.option('--author-name', default='Developer', help='Author name')
@click.option('--author-email', default='developer@example.com', help='Author email')
def create_openssl_project(template, project_name, openssl_version, 
                          deployment_target, enable_fips, author_name, author_email):
    """Create a new OpenSSL project"""
    
    from ..templates import TemplateManager
    
    click.echo(f"🔐 Creating OpenSSL project: {project_name}")
    
    # Auto-enable FIPS for government deployment
    if deployment_target == 'fips-government':
        enable_fips = True
    
    variables = {
        'project_name': project_name,
        'openssl_version': openssl_version,
        'deployment_target': deployment_target,
        'enable_fips': enable_fips,
        'author_name': author_name,
        'author_email': author_email
    }
    
    try:
        template_manager = TemplateManager("templates")
        template_manager.apply_template(f"openssl/{template}", variables, project_name)
        
        click.echo("✅ Project created successfully!")
        click.echo(f"\nNext steps:")
        click.echo(f"cd {project_name}")
        click.echo("conan remote add ${CONAN_REPOSITORY_NAME} ${CONAN_REPOSITORY_URL} --force")
        click.echo("conan install . --build=missing")
        click.echo("cmake --preset conan-default && cmake --build --preset conan-release")
        
        if enable_fips:
            click.echo("\n🔒 FIPS mode enabled for government deployment")
        
    except Exception as e:
        click.echo(f"❌ Failed to create project: {e}")

@click.command()
@click.option('--project-type', default='openssl', help='Project type')
@click.option('--platform', 
              type=click.Choice(['linux', 'windows', 'macos']),
              default='linux', help='Development platform')
@click.option('--force', is_flag=True, help='Overwrite existing .cursor/')
def deploy_cursor(project_type, platform, force):
    """Deploy Cursor AI configuration"""
    
    import os
    from pathlib import Path
    from ..cursor_deployer import CursorConfigDeployer
    
    click.echo(f"🤖 Deploying Cursor configuration for {project_type} on {platform}")
    
    repo_root = Path.cwd()
    package_root = Path(__file__).parent.parent.parent
    
    deployer = CursorConfigDeployer(repo_root, package_root)
    
    try:
        deployer.deploy(force=force, platform=platform, project_type=project_type)
        click.echo("✅ Cursor configuration deployed!")
        click.echo("\nNext steps:")
        click.echo("1. Open project in Cursor IDE")
        click.echo("2. Go to Settings > MCP and refresh")
        click.echo("3. Cursor will now have OpenSSL development context")
        
    except Exception as e:
        click.echo(f"❌ Failed to deploy Cursor config: {e}")
