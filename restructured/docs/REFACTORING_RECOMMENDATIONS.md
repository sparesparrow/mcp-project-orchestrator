# Refactoring Recommendations

## Executive Summary

This document outlines recommended refactoring and improvement opportunities for the MCP Project Orchestrator. The codebase is functional with all tests passing, but these improvements will enhance maintainability, performance, and extensibility.

## 🎯 Priority Matrix

| Priority | Impact | Effort | Recommendation |
|----------|---------|--------|----------------|
| P0 | High | Low | Config naming consolidation |
| P0 | High | Medium | Test coverage increase |
| P1 | High | Medium | Manager abstraction |
| P1 | Medium | Low | Error handling improvements |
| P2 | Medium | Medium | Plugin system |
| P2 | Low | Low | Code documentation |
| P3 | Medium | High | Performance optimization |

## 🔧 Critical Refactorings (P0)

### 1. Configuration Naming Consolidation

**Problem**: Inconsistent naming between `Config` and `MCPConfig`
- Tests import `MCPConfig`
- Some modules expect `Config`
- Creates confusion and maintenance burden

**Solution**:
```python
# Standardize on MCPConfig everywhere
# Update core/__init__.py
from .config import MCPConfig as Config, MCPConfig

# Update all imports to use MCPConfig consistently
# OR rename MCPConfig to Config in config.py
```

**Benefits**:
- Single source of truth
- Clearer imports
- Easier to understand

**Estimated Effort**: 2 hours
**Breaking Changes**: Minimal (alias preserves backward compatibility)

### 2. Test Coverage Improvement

**Current**: 27% overall coverage
**Target**: 80%+ coverage

**Focus Areas**:
```
Priority modules to test:
1. prompt_manager/manager.py (32% → 80%)
2. mermaid/generator.py (24% → 80%)
3. mermaid/renderer.py (43% → 80%)
4. core/config.py (61% → 85%)
```

**Approach**:
```python
# Add tests for:
# 1. Manager async methods
# 2. Edge cases and error conditions
# 3. Integration scenarios
# 4. Complex diagram generation

# Example new test:
def test_prompt_manager_async_operations(prompt_manager):
    """Test async prompt loading and caching."""
    # Test async load
    # Test cache behavior
    # Test concurrent access
```

**Estimated Effort**: 1-2 weeks
**Benefits**: Better reliability, easier refactoring, confidence in changes

## 🏗️ Structural Improvements (P1)

### 3. Abstract Manager Base Class

**Problem**: PromptManager and TemplateManager have duplicate patterns

**Current Structure**:
```python
# templates/__init__.py
class TemplateManager:
    def __init__(self, templates_dir): ...
    def discover_templates(self): ...
    def list_templates(self, filter): ...
    def get_template(self, name): ...

# prompt_manager/manager.py
class PromptManager:
    def __init__(self, config): ...
    def discover_prompts(self): ...
    def list_prompts(self, category): ...
    def get_prompt(self, name): ...
```

**Proposed Solution**:
```python
# core/managers.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')

class BaseResourceManager(ABC, Generic[T]):
    """Abstract base class for resource managers."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self._resources: Dict[str, T] = {}
    
    @abstractmethod
    def discover_resources(self) -> None:
        """Discover and load resources from base directory."""
        pass
    
    @abstractmethod
    def validate_resource(self, resource: T) -> bool:
        """Validate a resource."""
        pass
    
    def list_resources(self, **filters) -> List[str]:
        """List resources matching filters."""
        return list(self._resources.keys())
    
    def get_resource(self, name: str) -> Optional[T]:
        """Get a resource by name."""
        return self._resources.get(name)
    
    def save_resource(self, name: str, resource: T) -> None:
        """Save a resource."""
        if not self.validate_resource(resource):
            raise ValueError(f"Invalid resource: {name}")
        self._resources[name] = resource

# Usage:
class TemplateManager(BaseResourceManager[BaseTemplate]):
    def discover_resources(self):
        # Template-specific discovery
        pass
    
    def validate_resource(self, resource):
        return resource.validate()
```

**Benefits**:
- DRY principle
- Consistent API
- Easier to add new managers
- Shared testing utilities

**Estimated Effort**: 1 week
**Breaking Changes**: Minimal (preserve existing public APIs)

### 4. Enhanced Error Handling

**Current Issues**:
- Generic exceptions lose context
- No error codes for programmatic handling
- Limited debugging information

**Proposed Solution**:
```python
# core/exceptions.py
from enum import Enum
from typing import Optional, Dict, Any

class ErrorCode(Enum):
    """Standard error codes for MCP operations."""
    TEMPLATE_NOT_FOUND = "E001"
    TEMPLATE_INVALID = "E002"
    VARIABLE_MISSING = "E003"
    DIAGRAM_INVALID = "E004"
    IO_ERROR = "E005"
    CONFIG_ERROR = "E006"

class MCPError(Exception):
    """Enhanced MCP exception with context."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message": str(self),
            "code": self.code.value,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }

class TemplateNotFoundError(MCPError):
    """Template not found."""
    def __init__(self, name: str):
        super().__init__(
            f"Template not found: {name}",
            ErrorCode.TEMPLATE_NOT_FOUND,
            {"template_name": name}
        )

# Usage:
def get_template(self, name: str) -> Template:
    if name not in self._templates:
        raise TemplateNotFoundError(name)
    return self._templates[name]
```

**Benefits**:
- Better debugging
- Programmatic error handling
- Detailed error reports
- Error tracking/monitoring

**Estimated Effort**: 3-4 days

## 🚀 Feature Enhancements (P2)

### 5. Plugin System

**Goal**: Allow external plugins for templates, diagrams, and tools

**Architecture**:
```python
# core/plugins.py
from typing import Protocol, List
from abc import abstractmethod

class TemplateProvider(Protocol):
    """Protocol for template providers."""
    
    @abstractmethod
    def list_templates(self) -> List[str]:
        """List available templates."""
        ...
    
    @abstractmethod
    def get_template(self, name: str) -> BaseTemplate:
        """Get a template by name."""
        ...

class PluginRegistry:
    """Central plugin registry."""
    
    def __init__(self):
        self._template_providers: List[TemplateProvider] = []
        self._diagram_renderers: List[DiagramRenderer] = []
    
    def register_template_provider(self, provider: TemplateProvider):
        """Register a template provider plugin."""
        self._template_providers.append(provider)
    
    def discover_plugins(self):
        """Discover plugins using entry points."""
        import importlib.metadata
        
        for entry_point in importlib.metadata.entry_points().select(
            group='mcp_orchestrator.plugins'
        ):
            plugin = entry_point.load()
            plugin.register(self)

# pyproject.toml
[project.entry-points."mcp_orchestrator.plugins"]
my_plugin = "my_package.plugin:register"
```

**Benefits**:
- Extensibility without core changes
- Third-party integrations
- Community contributions
- Isolated plugin failures

**Estimated Effort**: 2 weeks

### 6. Event System

**Goal**: Decouple components with event-driven architecture

**Implementation**:
```python
# core/events.py
from dataclasses import dataclass
from typing import Callable, List, Any
from enum import Enum

class EventType(Enum):
    TEMPLATE_APPLIED = "template.applied"
    PROJECT_CREATED = "project.created"
    DIAGRAM_GENERATED = "diagram.generated"
    PROMPT_RENDERED = "prompt.rendered"

@dataclass
class Event:
    """Base event class."""
    type: EventType
    data: Any
    source: str

class EventBus:
    """Simple event bus for pub/sub."""
    
    def __init__(self):
        self._listeners: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)
    
    def publish(self, event: Event):
        """Publish an event."""
        for handler in self._listeners.get(event.type, []):
            try:
                handler(event)
            except Exception as e:
                # Log but don't fail
                logger.error(f"Event handler failed: {e}")

# Usage:
event_bus = EventBus()

# Subscribe
def on_template_applied(event: Event):
    logger.info(f"Template applied: {event.data['name']}")

event_bus.subscribe(EventType.TEMPLATE_APPLIED, on_template_applied)

# Publish
event_bus.publish(Event(
    type=EventType.TEMPLATE_APPLIED,
    data={"name": "fastapi-project"},
    source="TemplateManager"
))
```

**Benefits**:
- Loose coupling
- Extensible workflows
- Audit logging
- Monitoring hooks

**Estimated Effort**: 1 week

## 📊 Performance Optimizations (P3)

### 7. Caching Strategy

**Current**: Minimal caching, repeated file I/O

**Proposed**:
```python
# core/cache.py
from functools import lru_cache, wraps
from typing import Callable, Any
import hashlib
import pickle
from pathlib import Path

class FileCache:
    """File-backed cache for expensive operations."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str) -> Any:
        """Get cached value."""
        cache_file = self.cache_dir / self._hash_key(key)
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def set(self, key: str, value: Any):
        """Set cached value."""
        cache_file = self.cache_dir / self._hash_key(key)
        with open(cache_file, 'wb') as f:
            pickle.dump(value, f)
    
    def _hash_key(self, key: str) -> str:
        """Hash key for filename."""
        return hashlib.sha256(key.encode()).hexdigest()

def cached_property(func: Callable) -> property:
    """Cached property decorator."""
    attr_name = f'_cached_{func.__name__}'
    
    @wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return property(wrapper)

# Usage:
class TemplateManager:
    @cached_property
    def available_templates(self) -> List[str]:
        """Cached list of templates."""
        return self._discover_templates()
```

**Estimated Effort**: 3-4 days

### 8. Async Operations

**Current**: Synchronous I/O blocks

**Proposed**:
```python
# Use async for I/O-bound operations
import asyncio
import aiofiles

class AsyncTemplateManager:
    async def load_template(self, name: str) -> Template:
        """Load template asynchronously."""
        path = self.templates_dir / f"{name}.json"
        async with aiofiles.open(path) as f:
            content = await f.read()
            return Template.from_json(content)
    
    async def load_all_templates(self) -> List[Template]:
        """Load all templates concurrently."""
        template_files = list(self.templates_dir.glob("*.json"))
        tasks = [self.load_template(f.stem) for f in template_files]
        return await asyncio.gather(*tasks)
```

**Estimated Effort**: 1 week

## 🧹 Code Quality Improvements

### 9. Type Hints Enhancement

**Current**: Basic type hints
**Target**: Comprehensive type coverage

```python
# Use Protocol for duck typing
from typing import Protocol

class Renderable(Protocol):
    """Protocol for renderable objects."""
    def render(self, context: Dict[str, Any]) -> str: ...

def render_template(template: Renderable, context: Dict[str, Any]) -> str:
    return template.render(context)

# Use Generic types
from typing import Generic, TypeVar

T = TypeVar('T', bound=BaseTemplate)

class TemplateRegistry(Generic[T]):
    def __init__(self):
        self._templates: Dict[str, T] = {}
    
    def register(self, name: str, template: T) -> None:
        self._templates[name] = template
    
    def get(self, name: str) -> Optional[T]:
        return self._templates.get(name)
```

### 10. Documentation Generation

**Setup Sphinx for API docs**:

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Generate docs
sphinx-quickstart docs
sphinx-apidoc -o docs/api src/mcp_project_orchestrator
sphinx-build -b html docs docs/_build
```

**Configuration**:
```python
# docs/conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

html_theme = 'sphinx_rtd_theme'
```

## 📋 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Config naming consolidation
- [ ] Test coverage to 50%
- [ ] Enhanced error handling

### Phase 2: Structure (Week 3-4)
- [ ] Abstract manager base class
- [ ] Test coverage to 65%
- [ ] Event system basics

### Phase 3: Features (Week 5-7)
- [ ] Plugin system
- [ ] Test coverage to 80%
- [ ] Caching implementation

### Phase 4: Polish (Week 8)
- [ ] Documentation generation
- [ ] Performance profiling
- [ ] Final testing and cleanup

## 🎯 Success Metrics

### Before Refactoring
- Test Coverage: 27%
- Modules: 36
- Code Smells: Medium
- Maintainability: Good

### After Refactoring (Target)
- Test Coverage: 80%+
- Modules: ~40 (well-organized)
- Code Smells: Low
- Maintainability: Excellent
- Performance: 2x faster template operations
- Plugin Ecosystem: 3+ community plugins

## 🔍 Code Review Checklist

For each refactoring:
- [ ] Tests updated and passing
- [ ] Documentation updated
- [ ] Type hints complete
- [ ] No breaking changes (or documented)
- [ ] Performance not regressed
- [ ] Security considered
- [ ] Accessibility maintained
- [ ] CI/CD passing

## 📚 References

- [Python Design Patterns](https://refactoring.guru/design-patterns/python)
- [Effective Python](https://effectivepython.com/)
- [Python Type Hints PEP 484](https://peps.python.org/pep-0484/)
- [Plugin Architecture in Python](https://realpython.com/python-application-layouts/)

---

**Last Updated**: 2025-10-01  
**Maintainer**: MCP Project Orchestrator Team
