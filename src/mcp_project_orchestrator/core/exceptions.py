"""Custom exceptions for MCP Project Orchestrator.

This module defines custom exceptions used throughout the project for specific error cases.
"""

class MCPException(Exception):
    """Base exception class for MCP Project Orchestrator."""

    def __init__(self, message: str, *args):
        """Initialize the exception.

        Args:
            message: Error message
            *args: Additional arguments
        """
        super().__init__(message, *args)
        self.message = message


class TemplateError(MCPException):
    """Exception raised for template-related errors."""

    def __init__(self, message: str, template_path: str = None):
        """Initialize the exception.

        Args:
            message: Error message
            template_path: Optional path to the template that caused the error
        """
        super().__init__(message)
        self.template_path = template_path


class PromptError(MCPException):
    """Exception raised for prompt-related errors."""

    def __init__(self, message: str, prompt_name: str = None):
        """Initialize the exception.

        Args:
            message: Error message
            prompt_name: Optional name of the prompt that caused the error
        """
        super().__init__(message)
        self.prompt_name = prompt_name


class MermaidError(MCPException):
    """Exception raised for Mermaid diagram generation errors."""

    def __init__(self, message: str, diagram_type: str = None):
        """Initialize the exception.

        Args:
            message: Error message
            diagram_type: Optional type of diagram that caused the error
        """
        super().__init__(message)
        self.diagram_type = diagram_type


class ConfigError(MCPException):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str, config_path: str = None):
        """Initialize the exception.

        Args:
            message: Error message
            config_path: Optional path to the configuration that caused the error
        """
        super().__init__(message)
        self.config_path = config_path


class ValidationError(MCPException):
    """Exception raised for validation errors."""

    def __init__(self, message: str, validation_errors: list = None):
        """Initialize the exception.

        Args:
            message: Error message
            validation_errors: Optional list of validation errors
        """
        super().__init__(message)
        self.validation_errors = validation_errors or []


class ResourceError(MCPException):
    """Exception raised for resource-related errors."""

    def __init__(self, message: str, resource_path: str = None):
        """Initialize the exception.

        Args:
            message: Error message
            resource_path: Optional path to the resource that caused the error
        """
        super().__init__(message)
        self.resource_path = resource_path 