"""Tests for exception handling."""

import pytest
from mcp_project_orchestrator.core.exceptions import (
    MCPException,
    ConfigError,
    TemplateError,
    PromptError,
    MermaidError,
    ValidationError,
    ResourceError
)


def test_mcp_exception_basic():
    """Test basic MCPException."""
    exc = MCPException("Test error")
    assert "Test error" in str(exc)
    assert exc.message == "Test error"
    assert isinstance(exc, Exception)
    assert hasattr(exc, 'code')
    assert hasattr(exc, 'details')


def test_config_error():
    """Test ConfigError."""
    exc = ConfigError("Invalid config", "/path/to/config")
    assert "Invalid config" in str(exc)
    assert exc.config_path == "/path/to/config"
    assert exc.message == "Invalid config"
    assert isinstance(exc, MCPException)


def test_template_error():
    """Test TemplateError."""
    exc = TemplateError("Template not found", "/path/to/template")
    assert "Template not found" in str(exc)
    assert exc.template_path == "/path/to/template"
    assert exc.message == "Template not found"
    assert isinstance(exc, MCPException)


def test_prompt_error():
    """Test PromptError."""
    exc = PromptError("Prompt failed", "my-prompt")
    assert "Prompt failed" in str(exc)
    assert exc.prompt_name == "my-prompt"
    assert exc.message == "Prompt failed"
    assert isinstance(exc, MCPException)


def test_mermaid_error():
    """Test MermaidError."""
    exc = MermaidError("Diagram generation failed", "flowchart")
    assert "Diagram generation failed" in str(exc)
    assert exc.diagram_type == "flowchart"
    assert exc.message == "Diagram generation failed"
    assert isinstance(exc, MCPException)


def test_validation_error():
    """Test ValidationError."""
    errors = ["error1", "error2"]
    exc = ValidationError("Validation failed", errors)
    assert "Validation failed" in str(exc)
    assert exc.validation_errors == errors
    assert exc.message == "Validation failed"
    assert isinstance(exc, MCPException)


def test_resource_error():
    """Test ResourceError."""
    exc = ResourceError("Resource missing", "/path/to/resource")
    assert "Resource missing" in str(exc)
    assert exc.resource_path == "/path/to/resource"
    assert exc.message == "Resource missing"
    assert isinstance(exc, MCPException)


def test_exception_hierarchy():
    """Test exception inheritance hierarchy."""
    # All custom exceptions should inherit from MCPException
    assert issubclass(ConfigError, MCPException)
    assert issubclass(TemplateError, MCPException)
    assert issubclass(PromptError, MCPException)
    assert issubclass(MermaidError, MCPException)
    assert issubclass(ValidationError, MCPException)
    assert issubclass(ResourceError, MCPException)
    
    # MCPException should inherit from Exception
    assert issubclass(MCPException, Exception)


def test_exception_catching():
    """Test that exceptions can be caught properly."""
    try:
        raise TemplateError("Test template error")
    except MCPException as e:
        assert "Test template error" in str(e)
    except Exception:
        pytest.fail("Should have caught as MCPException")


def test_exception_with_cause():
    """Test exception with underlying cause."""
    try:
        try:
            raise ValueError("Original error")
        except ValueError as e:
            raise TemplateError("Template error", cause=e) from e
    except TemplateError as e:
        assert "Template error" in str(e)
        assert isinstance(e.__cause__, ValueError)
        assert e.cause == e.__cause__
