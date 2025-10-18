"""Base classes for MCP Project Orchestrator components.

This module provides abstract base classes that define the core interfaces
for templates, components, and managers in the MCP Project Orchestrator.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class BaseComponent(ABC):
    """Abstract base class for all MCP components."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize a base component.

        Args:
            name: The name of the component
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up component resources."""
        pass


class BaseTemplate(ABC):
    """Abstract base class for all MCP templates."""

    def __init__(self, template_path: Union[str, Path]):
        """Initialize a base template.

        Args:
            template_path: Path to the template file or directory
        """
        self.template_path = Path(template_path)

    @abstractmethod
    async def render(self, context: Dict[str, Any]) -> str:
        """Render the template with the given context.

        Args:
            context: Dictionary containing template variables

        Returns:
            str: The rendered template
        """
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """Validate the template structure and content.

        Returns:
            bool: True if valid, False otherwise
        """
        pass


class BaseManager(ABC):
    """Abstract base class for all MCP managers."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize a base manager.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.components: Dict[str, BaseComponent] = {}

    @abstractmethod
    async def load_config(self) -> None:
        """Load manager configuration."""
        pass

    @abstractmethod
    async def register_component(self, component: BaseComponent) -> None:
        """Register a new component with the manager.

        Args:
            component: The component to register
        """
        pass

    @abstractmethod
    async def get_component(self, name: str) -> Optional[BaseComponent]:
        """Get a registered component by name.

        Args:
            name: Name of the component

        Returns:
            Optional[BaseComponent]: The component if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_components(self) -> List[str]:
        """List all registered components.

        Returns:
            List[str]: List of component names
        """
        pass 

class BaseOrchestrator(BaseComponent):
    """Base class for orchestrator components.
    
    This class provides a common interface for components that manage
    resources and interact with other parts of the system.
    """
    
    def __init__(self, config):
        """Initialize a base orchestrator.
        
        Args:
            config: Configuration instance
        """
        super().__init__(name=config.name if hasattr(config, "name") else "orchestrator", config=config)
        self.config = config
