"""
Cursor configuration management utilities.

This module provides classes and utilities for managing Cursor IDE
configuration files and settings.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CursorRule:
    """Represents a Cursor rule configuration."""
    
    title: str
    description: str
    platform: str
    content: str
    created: str
    user: str
    
    def to_mdc_content(self) -> str:
        """Convert to .mdc file content with YAML frontmatter."""
        frontmatter = {
            "title": self.title,
            "description": self.description,
            "platform": self.platform,
            "created": self.created,
            "user": self.user,
        }
        
        yaml_content = "\n".join([
            "---",
            *[f"{k}: {v}" for k, v in frontmatter.items()],
            "---",
            "",
        ])
        
        return yaml_content + self.content


@dataclass
class MCPServerConfig:
    """Represents an MCP server configuration."""
    
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    disabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        config = {
            "command": self.command,
            "args": self.args,
            "env": self.env,
        }
        
        if self.disabled:
            config["disabled"] = True
            
        return config


class CursorConfig:
    """Manages Cursor IDE configuration files."""
    
    def __init__(self, cursor_dir: Path):
        self.cursor_dir = Path(cursor_dir)
        self.rules_dir = self.cursor_dir / "rules"
        self.prompts_dir = self.cursor_dir / "prompts"
        self.mcp_config_file = self.cursor_dir / "mcp.json"
    
    def create_directory_structure(self) -> None:
        """Create the standard .cursor directory structure."""
        self.cursor_dir.mkdir(exist_ok=True)
        self.rules_dir.mkdir(exist_ok=True)
        self.prompts_dir.mkdir(exist_ok=True)
        (self.rules_dir / "custom").mkdir(exist_ok=True)
    
    def write_rule(self, rule: CursorRule, filename: str) -> None:
        """Write a rule to the rules directory."""
        rule_file = self.rules_dir / f"{filename}.mdc"
        rule_file.write_text(rule.to_mdc_content())
    
    def write_prompt(self, title: str, content: str, filename: str) -> None:
        """Write a prompt to the prompts directory."""
        prompt_file = self.prompts_dir / f"{filename}.md"
        prompt_file.write_text(f"# {title}\n\n{content}")
    
    def write_mcp_config(self, servers: List[MCPServerConfig], 
                        global_shortcut: str = "Ctrl+Shift+.",
                        logging_level: str = "info") -> None:
        """Write MCP server configuration."""
        config = {
            "mcpServers": {
                server.name: server.to_dict() 
                for server in servers
            },
            "globalShortcut": global_shortcut,
            "logging": {
                "level": logging_level
            }
        }
        
        self.mcp_config_file.write_text(json.dumps(config, indent=2))
    
    def create_gitignore(self) -> None:
        """Create .gitignore for .cursor directory."""
        gitignore_content = """# Cursor IDE local customizations
*.log
*.cache
.cursor-session

# Keep rule templates and prompts in VCS
!rules/
!prompts/
!mcp.json

# Ignore developer-specific overrides
rules/custom/
"""
        gitignore_file = self.cursor_dir / ".gitignore"
        gitignore_file.write_text(gitignore_content)
    
    def get_existing_rules(self) -> List[str]:
        """Get list of existing rule files."""
        if not self.rules_dir.exists():
            return []
        
        return [f.stem for f in self.rules_dir.glob("*.mdc")]
    
    def get_existing_prompts(self) -> List[str]:
        """Get list of existing prompt files."""
        if not self.prompts_dir.exists():
            return []
        
        return [f.stem for f in self.prompts_dir.glob("*.md")]
    
    def has_mcp_config(self) -> bool:
        """Check if MCP configuration exists."""
        return self.mcp_config_file.exists()
    
    def read_mcp_config(self) -> Optional[Dict[str, Any]]:
        """Read existing MCP configuration."""
        if not self.has_mcp_config():
            return None
        
        try:
            return json.loads(self.mcp_config_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    
    def is_configured(self) -> bool:
        """Check if Cursor is configured (has rules or prompts)."""
        return (
            len(self.get_existing_rules()) > 0 or 
            len(self.get_existing_prompts()) > 0 or
            self.has_mcp_config()
        )