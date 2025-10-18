"""
Abstract base classes for resource managers.

This module provides base manager classes that can be extended for managing
different types of resources (templates, prompts, diagrams, etc.).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar, Dict, List, Optional, Union
import json
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseResourceManager(ABC, Generic[T]):
    """Abstract base class for resource managers.
    
    This class provides a common interface and shared functionality for managing
    resources like templates, prompts, and diagrams. It handles:
    - Resource discovery and loading
    - Resource storage and retrieval
    - Resource validation
    - Category and tag management
    
    Type Parameters:
        T: The type of resource being managed
    
    Attributes:
        base_dir: Base directory for resource files
        _resources: Dictionary mapping resource names to resources
        _categories: Set of resource categories
        _tags: Set of resource tags
    """
    
    def __init__(self, base_dir: Union[str, Path]):
        """Initialize the resource manager.
        
        Args:
            base_dir: Base directory containing resource files
        """
        self.base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
        self._resources: Dict[str, T] = {}
        self._categories: set = set()
        self._tags: set = set()
    
    @abstractmethod
    def discover_resources(self) -> None:
        """Discover and load resources from the base directory.
        
        This method should:
        1. Scan the base directory for resource files
        2. Load each resource
        3. Validate the resource
        4. Store the resource in _resources
        5. Update _categories and _tags
        
        Raises:
            FileNotFoundError: If base_dir doesn't exist
            ValueError: If resource validation fails
        """
        pass
    
    @abstractmethod
    def validate_resource(self, resource: T) -> bool:
        """Validate a resource.
        
        Args:
            resource: Resource to validate
            
        Returns:
            True if resource is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def load_resource(self, path: Path) -> T:
        """Load a resource from a file.
        
        Args:
            path: Path to the resource file
            
        Returns:
            Loaded resource instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file content is invalid
        """
        pass
    
    @abstractmethod
    def save_resource(self, name: str, resource: T) -> None:
        """Save a resource to disk.
        
        Args:
            name: Resource name
            resource: Resource to save
            
        Raises:
            ValueError: If resource is invalid
        """
        pass
    
    def list_resources(self, **filters) -> List[str]:
        """List resource names matching optional filters.
        
        Args:
            **filters: Optional filters (category, tag, etc.)
            
        Returns:
            List of resource names
        """
        if not filters:
            return list(self._resources.keys())
        
        results = []
        for name, resource in self._resources.items():
            match = True
            
            # Apply filters
            if 'category' in filters:
                if not self._matches_category(resource, filters['category']):
                    match = False
            
            if 'tag' in filters:
                if not self._matches_tag(resource, filters['tag']):
                    match = False
            
            if match:
                results.append(name)
        
        return results
    
    def get_resource(self, name: str) -> Optional[T]:
        """Get a resource by name.
        
        Args:
            name: Resource name
            
        Returns:
            Resource instance or None if not found
        """
        return self._resources.get(name)
    
    def has_resource(self, name: str) -> bool:
        """Check if a resource exists.
        
        Args:
            name: Resource name
            
        Returns:
            True if resource exists, False otherwise
        """
        return name in self._resources
    
    def add_resource(self, name: str, resource: T) -> None:
        """Add a resource to the manager.
        
        Args:
            name: Resource name
            resource: Resource to add
            
        Raises:
            ValueError: If resource is invalid
            FileExistsError: If resource already exists
        """
        if not self.validate_resource(resource):
            raise ValueError(f"Invalid resource: {name}")
        
        if name in self._resources:
            raise FileExistsError(f"Resource already exists: {name}")
        
        self._resources[name] = resource
        self._update_metadata(resource)
    
    def update_resource(self, name: str, resource: T) -> None:
        """Update an existing resource.
        
        Args:
            name: Resource name
            resource: Updated resource
            
        Raises:
            ValueError: If resource is invalid
            KeyError: If resource doesn't exist
        """
        if name not in self._resources:
            raise KeyError(f"Resource not found: {name}")
        
        if not self.validate_resource(resource):
            raise ValueError(f"Invalid resource: {name}")
        
        self._resources[name] = resource
        self._rebuild_metadata()
    
    def remove_resource(self, name: str) -> bool:
        """Remove a resource.
        
        Args:
            name: Resource name
            
        Returns:
            True if resource was removed, False if not found
        """
        if name not in self._resources:
            return False
        
        del self._resources[name]
        self._rebuild_metadata()
        return True
    
    def get_categories(self) -> List[str]:
        """Get all resource categories.
        
        Returns:
            Sorted list of category names
        """
        return sorted(self._categories)
    
    def get_tags(self) -> List[str]:
        """Get all resource tags.
        
        Returns:
            Sorted list of tag names
        """
        return sorted(self._tags)
    
    def clear(self) -> None:
        """Clear all resources and metadata."""
        self._resources.clear()
        self._categories.clear()
        self._tags.clear()
    
    def _update_metadata(self, resource: T) -> None:
        """Update metadata from a single resource.
        
        This method should extract categories and tags from the resource
        and add them to the manager's metadata sets.
        
        Args:
            resource: Resource to extract metadata from
        """
        # Subclasses should override if they have categories/tags
        pass
    
    def _rebuild_metadata(self) -> None:
        """Rebuild metadata from all resources.
        
        This method should rebuild the _categories and _tags sets by
        scanning all resources.
        """
        self._categories.clear()
        self._tags.clear()
        
        for resource in self._resources.values():
            self._update_metadata(resource)
    
    def _matches_category(self, resource: T, category: str) -> bool:
        """Check if resource matches a category filter.
        
        Args:
            resource: Resource to check
            category: Category to match
            
        Returns:
            True if resource matches, False otherwise
        """
        # Subclasses should override
        return True
    
    def _matches_tag(self, resource: T, tag: str) -> bool:
        """Check if resource matches a tag filter.
        
        Args:
            resource: Resource to check
            tag: Tag to match
            
        Returns:
            True if resource matches, False otherwise
        """
        # Subclasses should override
        return True
    
    def __len__(self) -> int:
        """Get the number of resources."""
        return len(self._resources)
    
    def __contains__(self, name: str) -> bool:
        """Check if a resource exists."""
        return name in self._resources
    
    def __iter__(self):
        """Iterate over resource names."""
        return iter(self._resources)
