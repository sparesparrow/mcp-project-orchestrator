"""Custom exceptions for MCP Project Orchestrator.

This module defines custom exceptions used throughout the project for specific error cases.
All exceptions include error codes for programmatic handling and detailed context for debugging.
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(Enum):
    """Standard error codes for MCP operations."""
    
    # General errors (E00x)
    UNKNOWN_ERROR = "E000"
    INTERNAL_ERROR = "E001"
    
    # Configuration errors (E01x)
    CONFIG_INVALID = "E010"
    CONFIG_MISSING = "E011"
    CONFIG_LOAD_FAILED = "E012"
    
    # Template errors (E02x)
    TEMPLATE_NOT_FOUND = "E020"
    TEMPLATE_INVALID = "E021"
    TEMPLATE_LOAD_FAILED = "E022"
    TEMPLATE_APPLY_FAILED = "E023"
    
    # Prompt errors (E03x)
    PROMPT_NOT_FOUND = "E030"
    PROMPT_INVALID = "E031"
    PROMPT_RENDER_FAILED = "E032"
    PROMPT_VARIABLE_MISSING = "E033"
    
    # Diagram errors (E04x)
    DIAGRAM_INVALID = "E040"
    DIAGRAM_GENERATION_FAILED = "E041"
    DIAGRAM_RENDER_FAILED = "E042"
    DIAGRAM_VALIDATION_FAILED = "E043"
    
    # Resource errors (E05x)
    RESOURCE_NOT_FOUND = "E050"
    RESOURCE_INVALID = "E051"
    RESOURCE_LOAD_FAILED = "E052"
    RESOURCE_SAVE_FAILED = "E053"
    
    # Validation errors (E06x)
    VALIDATION_FAILED = "E060"
    SCHEMA_INVALID = "E061"
    
    # I/O errors (E07x)
    FILE_NOT_FOUND = "E070"
    FILE_READ_ERROR = "E071"
    FILE_WRITE_ERROR = "E072"
    DIRECTORY_NOT_FOUND = "E073"


class MCPException(Exception):
    """Base exception class for MCP Project Orchestrator with enhanced error tracking.
    
    All MCP exceptions include:
    - A human-readable message
    - A standard error code for programmatic handling
    - Contextual details as a dictionary
    - Optional reference to the underlying cause
    
    Attributes:
        message: Human-readable error message
        code: Standard error code (ErrorCode enum)
        details: Dictionary with additional context
        cause: Optional underlying exception that caused this error
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception.

        Args:
            message: Human-readable error message
            code: Standard error code
            details: Optional dictionary with additional context
            cause: Optional underlying exception
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization.
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code.value,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }
    
    def __str__(self) -> str:
        """Get string representation of exception."""
        parts = [f"[{self.code.value}] {self.message}"]
        
        if self.details:
            parts.append(f"Details: {self.details}")
        
        if self.cause:
            parts.append(f"Caused by: {self.cause}")
        
        return " | ".join(parts)


class TemplateError(MCPException):
    """Exception raised for template-related errors."""

    def __init__(
        self,
        message: str,
        template_path: str = None,
        code: ErrorCode = ErrorCode.TEMPLATE_INVALID,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception.

        Args:
            message: Error message
            template_path: Optional path to the template that caused the error
            code: Error code (default: TEMPLATE_INVALID)
            cause: Optional underlying exception
        """
        details = {"template_path": template_path} if template_path else {}
        super().__init__(message, code, details, cause)
        self.template_path = template_path


class PromptError(MCPException):
    """Exception raised for prompt-related errors."""

    def __init__(
        self,
        message: str,
        prompt_name: str = None,
        code: ErrorCode = ErrorCode.PROMPT_INVALID,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception.

        Args:
            message: Error message
            prompt_name: Optional name of the prompt that caused the error
            code: Error code (default: PROMPT_INVALID)
            cause: Optional underlying exception
        """
        details = {"prompt_name": prompt_name} if prompt_name else {}
        super().__init__(message, code, details, cause)
        self.prompt_name = prompt_name


class MermaidError(MCPException):
    """Exception raised for Mermaid diagram generation errors."""

    def __init__(
        self,
        message: str,
        diagram_type: str = None,
        code: ErrorCode = ErrorCode.DIAGRAM_INVALID,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception.

        Args:
            message: Error message
            diagram_type: Optional type of diagram that caused the error
            code: Error code (default: DIAGRAM_INVALID)
            cause: Optional underlying exception
        """
        details = {"diagram_type": diagram_type} if diagram_type else {}
        super().__init__(message, code, details, cause)
        self.diagram_type = diagram_type


class ConfigError(MCPException):
    """Exception raised for configuration-related errors."""

    def __init__(
        self,
        message: str,
        config_path: str = None,
        code: ErrorCode = ErrorCode.CONFIG_INVALID,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception.

        Args:
            message: Error message
            config_path: Optional path to the configuration that caused the error
            code: Error code (default: CONFIG_INVALID)
            cause: Optional underlying exception
        """
        details = {"config_path": config_path} if config_path else {}
        super().__init__(message, code, details, cause)
        self.config_path = config_path


class ValidationError(MCPException):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str,
        validation_errors: list = None,
        code: ErrorCode = ErrorCode.VALIDATION_FAILED,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception.

        Args:
            message: Error message
            validation_errors: Optional list of validation errors
            code: Error code (default: VALIDATION_FAILED)
            cause: Optional underlying exception
        """
        details = {"validation_errors": validation_errors} if validation_errors else {}
        super().__init__(message, code, details, cause)
        self.validation_errors = validation_errors or []


class ResourceError(MCPException):
    """Exception raised for resource-related errors."""

    def __init__(
        self,
        message: str,
        resource_path: str = None,
        code: ErrorCode = ErrorCode.RESOURCE_INVALID,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception.

        Args:
            message: Error message
            resource_path: Optional path to the resource that caused the error
            code: Error code (default: RESOURCE_INVALID)
            cause: Optional underlying exception
        """
        details = {"resource_path": resource_path} if resource_path else {}
        super().__init__(message, code, details, cause)
        self.resource_path = resource_path 