"""
Cursor configuration deployment system.

This module provides the main deployment functionality for Cursor IDE
configuration, similar to how Conan manages build profiles.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from jinja2 import Template, Environment, FileSystemLoader
from datetime import datetime

from .platform_detector import PlatformDetector
from .cursor_config import CursorConfig, CursorRule, MCPServerConfig


class CursorConfigDeployer:
    """
    Deploy Cursor configuration templates to local repository.
    
    This class manages the deployment of Cursor IDE configuration files
    to a repository, similar to how Conan profiles are deployed.
    """
    
    def __init__(self, repo_root: Path, package_root: Path):
        """
        Initialize the deployer.
        
        Args:
            repo_root: Path to the target repository root
            package_root: Path to the mcp-project-orchestrator/openssl package root
        """
        self.repo_root = Path(repo_root).resolve()
        self.package_root = Path(package_root).resolve()
        self.cursor_dir = self.repo_root / ".cursor"
        self.templates_dir = self.package_root / "cursor-rules"
        
        self.platform_detector = PlatformDetector()
        self.cursor_config = CursorConfig(self.cursor_dir)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False
        )
    
    def detect_platform(self) -> Dict[str, Any]:
        """Detect developer platform and environment."""
        return self.platform_detector.detect_platform()
    
    def deploy(self, 
               force: bool = False, 
               custom_rules: Optional[List[Path]] = None,
               opt_out: bool = False) -> None:
        """
        Deploy Cursor configuration to repository.
        
        Args:
            force: Overwrite existing configuration
            custom_rules: List of paths to custom rule files to import
            opt_out: If True, skip deployment (developer doesn't want AI)
        """
        if opt_out:
            print("⏭️  Cursor configuration deployment skipped (opt-out)")
            return
        
        if self.cursor_dir.exists() and not force:
            print(f"ℹ️  .cursor/ already exists. Use --force to overwrite.")
            print(f"ℹ️  Or manually merge with: {self.cursor_dir}")
            return
        
        platform_info = self.detect_platform()
        
        print(f"🤖 Deploying Cursor configuration...")
        print(f"   Platform: {platform_info['os']} {platform_info['os_version']}")
        print(f"   User: {platform_info['user']}")
        print(f"   CI Environment: {platform_info['is_ci']}")
        
        # Create .cursor directory structure
        self.cursor_config.create_directory_structure()
        
        # Deploy platform-specific rules
        self._deploy_rules(platform_info)
        
        # Deploy prompts
        self._deploy_prompts(platform_info)
        
        # Deploy MCP configuration
        self._deploy_mcp_config(platform_info)
        
        # Import custom rules if provided
        if custom_rules:
            self._import_custom_rules(custom_rules)
        
        # Create .gitignore for .cursor/ (optional artifacts)
        self.cursor_config.create_gitignore()
        
        # Summary
        rule_count = len(self.cursor_config.get_existing_rules())
        prompt_count = len(self.cursor_config.get_existing_prompts())
        mcp_configured = self.cursor_config.has_mcp_config()
        
        print(f"✅ Cursor configuration deployed to {self.cursor_dir}")
        print(f"   Rules: {rule_count} files")
        print(f"   Prompts: {prompt_count} files")
        print(f"   MCP config: {'✅' if mcp_configured else '❌'}")
    
    def _deploy_rules(self, platform_info: Dict[str, Any]) -> None:
        """Deploy platform-specific rule files."""
        # Determine which rule template to use
        rule_template_name = self.platform_detector.get_rule_template_name()
        
        # Always deploy shared rules
        self._render_template(
            "rules/shared.mdc.jinja2",
            self.cursor_dir / "rules" / "shared.mdc",
            platform_info
        )
        
        # Deploy OS-specific rules
        os_specific_template = f"rules/{rule_template_name}.mdc.jinja2"
        if (self.templates_dir / os_specific_template).exists():
            self._render_template(
                os_specific_template,
                self.cursor_dir / "rules" / f"{rule_template_name}.mdc",
                platform_info
            )
        else:
            print(f"⚠️  No rule template for {os_specific_template}, skipping")
    
    def _deploy_prompts(self, platform_info: Dict[str, Any]) -> None:
        """Deploy prompt templates."""
        prompts_dir = self.templates_dir / "prompts"
        if not prompts_dir.exists():
            print("⚠️  No prompts directory found, skipping prompts")
            return
        
        for prompt_template in prompts_dir.glob("*.jinja2"):
            output_name = prompt_template.stem  # Remove .jinja2
            self._render_template(
                f"prompts/{prompt_template.name}",
                self.cursor_dir / "prompts" / output_name,
                platform_info
            )
    
    def _deploy_mcp_config(self, platform_info: Dict[str, Any]) -> None:
        """Deploy MCP server configuration."""
        mcp_template = self.templates_dir / "mcp.json.jinja2"
        if not mcp_template.exists():
            print("⚠️  No MCP configuration template found, skipping")
            return
        
        # Render MCP configuration
        context = platform_info.copy()
        context['platform_detector'] = self.platform_detector
        mcp_content = self._render_template_content(
            "mcp.json.jinja2",
            context
        )
        
        # Parse as JSON to validate
        import json
        try:
            mcp_config = json.loads(mcp_content)
            self.cursor_dir.mkdir(exist_ok=True)
            (self.cursor_dir / "mcp.json").write_text(mcp_content)
            print(f"  📄 mcp.json")
        except json.JSONDecodeError as e:
            print(f"⚠️  Invalid MCP configuration template: {e}")
    
    def _render_template(self, template_path: str, output_path: Path, context: Dict[str, Any]) -> None:
        """Render Jinja2 template with context."""
        try:
            template = self.jinja_env.get_template(template_path)
            rendered = template.render(**context)
            output_path.write_text(rendered)
            print(f"  📄 {output_path.relative_to(self.cursor_dir)}")
        except Exception as e:
            print(f"⚠️  Error rendering {template_path}: {e}")
    
    def _render_template_content(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 template and return content as string."""
        template = self.jinja_env.get_template(template_path)
        return template.render(**context)
    
    def _import_custom_rules(self, custom_rules: List[Path]) -> None:
        """Import developer's custom rule files."""
        custom_dir = self.cursor_dir / "rules" / "custom"
        custom_dir.mkdir(exist_ok=True)
        
        for custom_rule_path in custom_rules:
            if not custom_rule_path.exists():
                print(f"⚠️  Custom rule not found: {custom_rule_path}")
                continue
            
            dest = custom_dir / custom_rule_path.name
            shutil.copy2(custom_rule_path, dest)
            print(f"  📦 Imported custom rule: {dest.name}")
    
    def show_status(self) -> None:
        """Show current Cursor configuration status."""
        if not self.cursor_dir.exists():
            print("❌ No .cursor/ configuration found")
            print("   Run: mcp-orchestrator setup-cursor")
            return
        
        print(f"📁 Cursor configuration: {self.cursor_dir}")
        
        # Show rules
        rules = self.cursor_config.get_existing_rules()
        print(f"   Rules: {len(rules)} files")
        for rule in sorted(rules):
            print(f"     - {rule}.mdc")
        
        # Show prompts
        prompts = self.cursor_config.get_existing_prompts()
        print(f"   Prompts: {len(prompts)} files")
        for prompt in sorted(prompts):
            print(f"     - {prompt}.md")
        
        # Show MCP config
        mcp_configured = self.cursor_config.has_mcp_config()
        print(f"   MCP config: {'✅' if mcp_configured else '❌'}")
        
        if mcp_configured:
            mcp_config = self.cursor_config.read_mcp_config()
            if mcp_config and "mcpServers" in mcp_config:
                server_count = len(mcp_config["mcpServers"])
                print(f"     - {server_count} MCP servers configured")
    
    def dry_run(self) -> None:
        """Show what would be deployed without making changes."""
        print("🔍 Dry run mode - no files will be created")
        
        platform_info = self.detect_platform()
        print(f"   Platform: {platform_info['os']} {platform_info['os_version']}")
        print(f"   User: {platform_info['user']}")
        print(f"   Is CI: {platform_info['is_ci']}")
        print(f"   Target: {self.cursor_dir}")
        
        # Show what templates would be used
        rule_template = self.platform_detector.get_rule_template_name()
        print(f"   Rule template: {rule_template}.mdc.jinja2")
        
        # Check available templates
        templates_dir = self.templates_dir
        if templates_dir.exists():
            print(f"   Available templates:")
            for template_file in templates_dir.rglob("*.jinja2"):
                rel_path = template_file.relative_to(templates_dir)
                print(f"     - {rel_path}")
        else:
            print(f"   ⚠️  Templates directory not found: {templates_dir}")