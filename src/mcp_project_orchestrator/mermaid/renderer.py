"""
Mermaid diagram renderer for MCP Project Orchestrator.

This module provides functionality for rendering Mermaid diagram
definitions to various output formats using the Mermaid CLI.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Optional, Union, List

from ..core import BaseOrchestrator, Config
from .types import RenderConfig, RenderFormat

class MermaidRenderer(BaseOrchestrator):
    """Class for rendering Mermaid diagrams."""
    
    def __init__(self, config: Config):
        """Initialize the Mermaid renderer.
        
        Args:
            config: Configuration instance
        """
        super().__init__(config)
        self.cli_path = config.mermaid_cli_path
        self.output_dir = config.mermaid_output_dir
        
    async def initialize(self) -> None:
        """Initialize the renderer.
        
        Verifies that the Mermaid CLI is available and creates
        the output directory if it doesn't exist.
        
        Raises:
            RuntimeError: If Mermaid CLI is not found
        """
        if not self.cli_path or not Path(self.cli_path).exists():
            raise RuntimeError(
                "Mermaid CLI not found. Please install @mermaid-js/mermaid-cli "
                "and set the mermaid_cli_path in configuration."
            )
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
        
    async def render(
        self,
        definition: str,
        output_path: Optional[Path] = None,
        config: Optional[RenderConfig] = None,
    ) -> Path:
        """Render a Mermaid diagram.
        
        Args:
            definition: Mermaid diagram definition
            output_path: Optional path for the output file
            config: Optional rendering configuration
            
        Returns:
            Path to the rendered diagram file
            
        Raises:
            RuntimeError: If rendering fails
        """
        if config is None:
            config = RenderConfig()
            
        # Create temporary file for diagram definition
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False
        ) as temp_file:
            temp_file.write(definition)
            input_path = Path(temp_file.name)
            
        try:
            # Determine output path
            if output_path is None:
                output_path = self.output_dir / f"diagram_{input_path.stem}.{config.format}"
                
            # Create configuration file
            config_path = input_path.with_suffix(".json")
            with open(config_path, "w") as f:
                json.dump(config.to_dict(), f)
                
            # Build command
            cmd = [
                self.cli_path,
                "-i", str(input_path),
                "-o", str(output_path),
                "-c", str(config_path),
            ]
            
            # Run Mermaid CLI
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(
                    f"Mermaid CLI failed with code {process.returncode}: "
                    f"{stderr.decode()}"
                )
                
            return output_path
            
        finally:
            # Clean up temporary files
            input_path.unlink()
            config_path.unlink()
            
    async def render_to_string(
        self,
        definition: str,
        format: RenderFormat = RenderFormat.SVG,
        config: Optional[RenderConfig] = None,
    ) -> str:
        """Render a Mermaid diagram and return its contents as a string.
        
        Args:
            definition: Mermaid diagram definition
            format: Output format
            config: Optional rendering configuration
            
        Returns:
            String contents of the rendered diagram
            
        Raises:
            RuntimeError: If rendering fails
        """
        if config is None:
            config = RenderConfig(format=format)
        else:
            config.format = format
            
        output_path = await self.render(definition, config=config)
        
        try:
            with open(output_path) as f:
                return f.read()
        finally:
            output_path.unlink()
            
    def get_supported_formats(self) -> List[RenderFormat]:
        """Get list of supported output formats.
        
        Returns:
            List of supported RenderFormat values
        """
        return list(RenderFormat) 