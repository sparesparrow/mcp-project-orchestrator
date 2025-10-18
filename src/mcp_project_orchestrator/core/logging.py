"""
Logging configuration for MCP Project Orchestrator.

This module provides functions to set up and configure logging
for all components of the project orchestrator.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> None:
    """Set up logging configuration.
    
    Args:
        log_file: Optional path to log file. If not provided, logs to stderr
        level: Logging level (default: INFO)
        format_string: Optional custom format string for log messages
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
    handlers = []
    
    # Always add stderr handler
    handlers.append(logging.StreamHandler(sys.stderr))
    
    # Add file handler if log file is specified
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(str(log_file)))
        
    # Configure logging
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
    )
    
    # Set levels for third-party loggers
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Name for the logger
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name) 