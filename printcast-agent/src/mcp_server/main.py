#!/usr/bin/env python3
"""
Main entry point for PrintCast Agent MCP Server.

This script starts the MCP server and initializes all services.
"""

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.server import PrintCastMCPServer

# Load environment variables
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Server settings
    server_name: str = "PrintCast Agent"
    server_port: int = 8000
    debug: bool = False
    
    # Asterisk settings
    asterisk_host: str = "localhost"
    asterisk_port: int = 5038
    asterisk_username: str = "admin"
    asterisk_password: str = ""
    asterisk_context: str = "printcast-ivr"
    
    # ElevenLabs settings
    elevenlabs_api_key: str = ""
    elevenlabs_agent_id: Optional[str] = None
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    elevenlabs_model: str = "eleven_multilingual_v2"
    
    # Content settings
    github_token: Optional[str] = None
    news_api_key: Optional[str] = None
    rss_feeds: str = "https://news.ycombinator.com/rss,https://feeds.feedburner.com/TechCrunch/"
    
    # Printing settings
    default_printer: str = "default"
    cups_server: str = "localhost:631"
    print_temp_dir: str = "/tmp/printcast"
    
    # Delivery settings
    default_carrier: str = "post"
    sender_name: str = "PrintCast"
    sender_street: str = "Václavské náměstí 1"
    sender_city: str = "Praha"
    sender_postal_code: str = "11000"
    sender_country: str = "CZ"
    
    # Delivery API keys
    zasilkovna_api_key: Optional[str] = None
    dpd_api_key: Optional[str] = None
    ppl_api_key: Optional[str] = None
    
    # AWS settings (optional)
    aws_region: str = "eu-central-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def build_config(settings: Settings) -> Dict[str, Any]:
    """
    Build configuration dictionary from settings.
    
    Args:
        settings: Application settings
    
    Returns:
        Configuration dictionary
    """
    # Parse RSS feeds
    rss_feeds = [f.strip() for f in settings.rss_feeds.split(",") if f.strip()]
    
    config = {
        "asterisk": {
            "host": settings.asterisk_host,
            "port": settings.asterisk_port,
            "username": settings.asterisk_username,
            "password": settings.asterisk_password,
            "context": settings.asterisk_context,
        },
        "elevenlabs": {
            "api_key": settings.elevenlabs_api_key,
            "agent_id": settings.elevenlabs_agent_id,
            "voice_id": settings.elevenlabs_voice_id,
            "model": settings.elevenlabs_model,
        },
        "content": {
            "github_token": settings.github_token,
            "news_api_key": settings.news_api_key,
            "rss_feeds": rss_feeds,
            "cache_ttl": 3600,
        },
        "printing": {
            "default_printer": settings.default_printer,
            "cups_server": settings.cups_server,
            "temp_dir": settings.print_temp_dir,
            "pdf_settings": {
                "page_size": "A4",
                "margin": 20,
            },
        },
        "delivery": {
            "default_carrier": settings.default_carrier,
            "sender_address": {
                "name": settings.sender_name,
                "street": settings.sender_street,
                "city": settings.sender_city,
                "postal_code": settings.sender_postal_code,
                "country": settings.sender_country,
            },
            "carriers": {
                "post": {"enabled": True},
                "zasilkovna": {"enabled": bool(settings.zasilkovna_api_key)},
                "dpd": {"enabled": bool(settings.dpd_api_key)},
                "ppl": {"enabled": bool(settings.ppl_api_key)},
                "courier": {"enabled": True},
            },
            "api_keys": {
                "zasilkovna": settings.zasilkovna_api_key,
                "dpd": settings.dpd_api_key,
                "ppl": settings.ppl_api_key,
            },
        },
    }
    
    # Add AWS config if credentials provided
    if settings.aws_access_key_id:
        config["aws"] = {
            "region": settings.aws_region,
            "access_key_id": settings.aws_access_key_id,
            "secret_access_key": settings.aws_secret_access_key,
            "s3_bucket": settings.s3_bucket,
        }
    
    return config


async def main():
    """Main application entry point."""
    # Load settings
    settings = Settings()
    
    # Build configuration
    config = build_config(settings)
    
    # Create server
    server = PrintCastMCPServer(config)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received", signal=sig)
        asyncio.create_task(shutdown(server))
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start server
        logger.info(
            "Starting PrintCast MCP Server",
            server_name=settings.server_name,
            debug=settings.debug
        )
        
        await server.start()
        
    except Exception as e:
        logger.error("Server failed to start", error=str(e))
        sys.exit(1)


async def shutdown(server: PrintCastMCPServer):
    """
    Graceful shutdown handler.
    
    Args:
        server: Server instance to shutdown
    """
    try:
        logger.info("Shutting down server...")
        await server.stop()
        logger.info("Server shutdown complete")
        
        # Stop event loop
        loop = asyncio.get_event_loop()
        loop.stop()
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        sys.exit(1)