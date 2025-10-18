"""
Unified Mermaid Orchestrator Server - Combines Mermaid server functionality with orchestration capabilities.
"""

import os
import logging
import sys
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mermaid-orchestrator')

# Import from our modules
from .mermaid_server import MermaidServer, MermaidValidator, MermaidError
from src.solid.solid_server import SolidServer, SolidPrinciple
from src.orchestrator.code_diagram_orchestrator import (
    CodeDiagramOrchestrator,
    TaskScheduler,
    ResultSynthesizer
)

class MermaidOrchestratorServer(MermaidServer):
    """
    Enhanced Mermaid server with orchestration capabilities.
    
    This server inherits all standard Mermaid diagram capabilities and adds
    orchestration features for working with SOLID analysis.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_ttl: int = 3600,
        calls_per_minute: int = 25,
        orchestrator_calls_per_minute: int = 15
    ):
        """
        Initialize the enhanced Mermaid server with orchestration.
        
        Args:
            api_key: Anthropic API key
            cache_ttl: Cache time-to-live in seconds
            calls_per_minute: API rate limit for Mermaid operations
            orchestrator_calls_per_minute: API rate limit for orchestration operations
        """
        # Initialize the base Mermaid server
        super().__init__(api_key=api_key, cache_ttl=cache_ttl, calls_per_minute=calls_per_minute)
        
        # Initialize the orchestrator
        self.orchestrator = CodeDiagramOrchestrator(
            api_key=api_key,
            cache_ttl=cache_ttl,
            calls_per_minute=orchestrator_calls_per_minute
        )
        
        # Override the MCP server name
        self.mcp = self.orchestrator.mcp
        
        # Register the unified tools
        self.setup_unified_tools()
    
    def setup_unified_tools(self):
        """Set up both Mermaid and orchestration tools in a unified interface."""
        # Re-register Mermaid tools
        self.generate_diagram = self._register_generate_diagram()
        self.analyze_diagram = self._register_analyze_diagram()
        self.modify_diagram = self._register_modify_diagram()
        self.validate_diagram = self._register_validate_diagram()
        self.clear_cache = self._register_clear_cache()
        self.get_status = self._register_get_status()
        
        # Register orchestration tools
        self.analyze_and_visualize = self._register_analyze_and_visualize()
        self.generate_class_diagram = self._register_generate_class_diagram()
        self.create_documentation = self._register_create_documentation()
    
    def _register_analyze_and_visualize(self):
        """Register the analyze_and_visualize tool."""
        @self.mcp.tool()
        def analyze_and_visualize(code: str, principles: Optional[List[str]] = None) -> Dict[str, str]:
            """Analyze code against SOLID principles and generate a diagram from the results.
            
            Args:
                code: Code to analyze
                principles: Optional list of specific principles to check
                
            Returns:
                Dict containing analysis and diagram
            """
            return self.orchestrator.analyze_and_visualize(code, principles)
        
        return analyze_and_visualize
    
    def _register_generate_class_diagram(self):
        """Register the generate_class_diagram tool."""
        @self.mcp.tool()
        def generate_class_diagram(code: str) -> str:
            """Generate a class diagram from code.
            
            Args:
                code: Code to generate diagram from
                
            Returns:
                str: Mermaid diagram code
            """
            return self.orchestrator.generate_class_diagram(code)
        
        return generate_class_diagram
    
    def _register_create_documentation(self):
        """Register the create_documentation tool."""
        @self.mcp.tool()
        def create_documentation(code: str) -> str:
            """Create comprehensive documentation for code with analysis and diagrams.
            
            Args:
                code: Code to document
                
            Returns:
                str: Markdown documentation
            """
            return self.orchestrator.create_documentation(code)
        
        return create_documentation
    
    def get_unified_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the unified server.
        
        Returns:
            Dict containing status information
        """
        mermaid_status = super()._register_get_status()()
        orchestrator_status = self.orchestrator._register_get_status()()
        
        return {
            "mermaid_server": mermaid_status,
            "orchestrator": orchestrator_status,
            "server_type": "unified"
        }

def main():
    """Main entry point for the unified server."""
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY environment variable not set.")
        logger.warning("The server will fail to process requests without a valid API key.")
    
    # Get configuration from environment
    cache_ttl = int(os.environ.get("CACHE_TTL_SECONDS", "3600"))
    calls_per_minute = int(os.environ.get("CALLS_PER_MINUTE", "25"))
    orchestrator_calls_per_minute = int(os.environ.get("ORCHESTRATOR_CALLS_PER_MINUTE", "15"))
    
    # Start the unified server
    logger.info("Starting unified Mermaid Orchestrator MCP server")
    server = MermaidOrchestratorServer(
        cache_ttl=cache_ttl,
        calls_per_minute=calls_per_minute,
        orchestrator_calls_per_minute=orchestrator_calls_per_minute
    )
    server.run()

if __name__ == "__main__":
    main() 