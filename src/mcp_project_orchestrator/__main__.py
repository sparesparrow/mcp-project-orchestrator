"""
Command-line entry point for the MCP Project Orchestrator.
"""

import sys
import asyncio
import argparse
from pathlib import Path

from .server import start_server
from .core import setup_logging


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Project Orchestrator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--log-level", help="Logging level")
    
    args = parser.parse_args()
    
    # Look for config file in standard locations
    config_path = args.config
    if not config_path:
        # Check common config locations
        config_locations = [
            Path.cwd() / "config" / "default.json",
            Path.home() / ".config" / "mcp-project-orchestrator" / "config.json",
            Path("/etc/mcp-project-orchestrator/config.json")
        ]
        
        for location in config_locations:
            if location.exists():
                config_path = str(location)
                break
    
    # Set up logging early
    logger = setup_logging(log_file=args.log_file)
    
    try:
        # Start the server
        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(start_server(config_path))
        
        # Run the server
        loop.run_forever()
    except KeyboardInterrupt:
        # Handle graceful shutdown
        logger.info("Shutting down server...")
        loop.run_until_complete(server.stop())
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)
    finally:
        loop.close()
    
    
if __name__ == "__main__":
    main()
