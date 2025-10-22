"""Deploy Cursor configuration to local repository (profile management pattern)"""
from pathlib import Path
from jinja2 import Template
import platform
import os
import shutil

class CursorConfigDeployer:
    """Deploy Cursor configuration templates to local repository"""
    
    def __init__(self, repo_root: Path, package_root: Path):
        self.repo_root = Path(repo_root)
        self.package_root = Path(package_root)
        self.cursor_dir = self.repo_root / ".cursor"
        self.templates_dir = self.package_root / "cursor-templates"
    
    def deploy(self, force: bool = False, platform: str = None, project_type: str = "openssl"):
        """Deploy Cursor configuration to repository"""
        
        if self.cursor_dir.exists() and not force:
            print(f"ℹ️  .cursor/ already exists. Use --force to overwrite.")
            return
        
        # Auto-detect platform if not specified
        if platform is None:
            platform = platform.system().lower()
        
        platform_info = {
            "os": platform,
            "project_type": project_type,
            "user": os.getenv("USER", "developer"),
            "home": str(Path.home()),
            "repo_root": str(self.repo_root)
        }
        
        # Create .cursor directory structure
        self.cursor_dir.mkdir(exist_ok=True)
        (self.cursor_dir / "rules").mkdir(exist_ok=True)
        
        # Deploy platform-specific rules
        self._deploy_rules(platform_info, platform, project_type)
        
        # Deploy MCP configuration
        self._deploy_mcp_config(platform_info, project_type)
        
        print(f"✅ Cursor configuration deployed to {self.cursor_dir}")
        print(f"   Platform: {platform}")
        print(f"   Project type: {project_type}")
    
    def _deploy_rules(self, platform_info: dict, platform: str, project_type: str):
        """Deploy platform-specific rule files"""
        
        # Deploy shared rules
        shared_template = self.templates_dir / project_type / "shared.mdc.jinja2"
        if shared_template.exists():
            self._render_template(
                shared_template,
                self.cursor_dir / "rules" / "shared.mdc",
                platform_info
            )
        
        # Deploy platform-specific rules
        platform_template = self.templates_dir / project_type / f"{platform}-dev.mdc.jinja2"
        if platform_template.exists():
            self._render_template(
                platform_template,
                self.cursor_dir / "rules" / f"{platform}-dev.mdc",
                platform_info
            )
    
    def _deploy_mcp_config(self, platform_info: dict, project_type: str):
        """Deploy MCP server configuration"""
        
        # Create basic MCP configuration
        mcp_config = {
            "mcpServers": {
                "mcp-project-orchestrator": {
                    "command": "python",
                    "args": ["-m", "mcp_project_orchestrator"],
                    "env": {
                        "PROJECT_TYPE": project_type,
                        "PLATFORM": platform_info["os"]
                    }
                }
            }
        }
        
        import json
        (self.cursor_dir / "mcp.json").write_text(json.dumps(mcp_config, indent=2))
    
    def _render_template(self, template_path: Path, output_path: Path, context: dict):
        """Render Jinja2 template with context"""
        template = Template(template_path.read_text())
        rendered = template.render(**context)
        output_path.write_text(rendered)
        print(f"  📄 {output_path.relative_to(self.cursor_dir)}")
