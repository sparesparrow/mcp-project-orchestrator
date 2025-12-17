"""Tests for base classes."""

import pytest
from pathlib import Path
from mcp_project_orchestrator.core.base import (
    BaseComponent,
    BaseTemplate,
    BaseManager,
    BaseOrchestrator
)


class ConcreteComponent(BaseComponent):
    """Concrete implementation for testing."""
    
    async def initialize(self):
        self.initialized = True
    
    async def cleanup(self):
        self.cleaned_up = True


class ConcreteTemplate(BaseTemplate):
    """Concrete implementation for testing."""
    
    async def render(self, context):
        return f"Rendered: {context.get('name', 'unknown')}"
    
    async def validate(self):
        return self.template_path.exists() if hasattr(self, 'template_path') else True


class ConcreteManager(BaseManager):
    """Concrete implementation for testing."""
    
    async def load_config(self):
        self.config_loaded = True
    
    async def register_component(self, component):
        self.components[component.name] = component
    
    async def get_component(self, name):
        return self.components.get(name)
    
    async def list_components(self):
        return list(self.components.keys())


class ConcreteOrchestrator(BaseOrchestrator):
    """Concrete implementation for testing."""
    
    async def initialize(self):
        self.initialized = True
    
    async def cleanup(self):
        self.cleaned_up = True


@pytest.mark.asyncio
async def test_base_component():
    """Test BaseComponent."""
    component = ConcreteComponent("test-component", {"key": "value"})
    
    assert component.name == "test-component"
    assert component.config == {"key": "value"}
    
    await component.initialize()
    assert component.initialized is True
    
    await component.cleanup()
    assert component.cleaned_up is True


@pytest.mark.asyncio
async def test_base_template(tmp_path):
    """Test BaseTemplate."""
    template_file = tmp_path / "template.txt"
    template_file.write_text("Test template")
    
    template = ConcreteTemplate(template_file)
    assert template.template_path == template_file
    
    # Test render
    result = await template.render({"name": "Test"})
    assert result == "Rendered: Test"
    
    # Test validate
    is_valid = await template.validate()
    assert is_valid is True


@pytest.mark.asyncio
async def test_base_manager(tmp_path):
    """Test BaseManager."""
    config_file = tmp_path / "config.json"
    manager = ConcreteManager(config_file)
    
    assert manager.config_path == config_file
    assert manager.components == {}
    
    # Test load config
    await manager.load_config()
    assert manager.config_loaded is True
    
    # Test component registration
    component = ConcreteComponent("comp1", {})
    await manager.register_component(component)
    
    # Test get component
    retrieved = await manager.get_component("comp1")
    assert retrieved is component
    
    # Test list components
    components = await manager.list_components()
    assert components == ["comp1"]


@pytest.mark.asyncio
async def test_base_orchestrator():
    """Test BaseOrchestrator."""
    class MockConfig:
        name = "test-orchestrator"
    
    config = MockConfig()
    orchestrator = ConcreteOrchestrator(config)
    
    assert orchestrator.config is config
    assert orchestrator.name == "test-orchestrator"
    
    await orchestrator.initialize()
    assert orchestrator.initialized is True
    
    await orchestrator.cleanup()
    assert orchestrator.cleaned_up is True


def test_base_component_without_config():
    """Test BaseComponent without config."""
    component = ConcreteComponent("test")
    assert component.name == "test"
    assert component.config == {}


def test_abstract_methods():
    """Test that abstract methods must be implemented."""
    # BaseComponent requires initialize and cleanup
    with pytest.raises(TypeError):
        class IncompleteComponent(BaseComponent):
            async def initialize(self):
                pass
            # Missing cleanup
        IncompleteComponent("test")
    
    # BaseTemplate requires render and validate
    with pytest.raises(TypeError):
        class IncompleteTemplate(BaseTemplate):
            async def render(self, context):
                pass
            # Missing validate
        IncompleteTemplate(Path("test"))
