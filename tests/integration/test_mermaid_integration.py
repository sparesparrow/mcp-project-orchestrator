"""
Integration tests for the mermaid module.

These tests verify that the mermaid module components work together properly.
"""

import os
import pytest
import tempfile
from pathlib import Path
import json

from mcp_project_orchestrator.core import MCPConfig
from mcp_project_orchestrator.mermaid import MermaidGenerator
from mcp_project_orchestrator.mermaid import MermaidRenderer
from mcp_project_orchestrator.mermaid import DiagramType


class TestMermaidIntegration:
    """Integration tests for mermaid module components."""
    
    @pytest.fixture
    def temp_mermaid_dir(self):
        """Create a temporary mermaid directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mermaid_dir = Path(temp_dir) / "mermaid"
            mermaid_dir.mkdir(exist_ok=True)
            (mermaid_dir / "templates").mkdir(exist_ok=True)
            (mermaid_dir / "output").mkdir(exist_ok=True)
            yield mermaid_dir
    
    @pytest.fixture
    def config(self, temp_mermaid_dir):
        """Create a test configuration."""
        config_data = {
            "name": "test-mermaid",
            "version": "0.1.0",
            "description": "Test Mermaid Generator",
            "paths": {
                "mermaid_templates": str(temp_mermaid_dir / "templates"),
                "mermaid_output": str(temp_mermaid_dir / "output"),
                "mermaid_cli": "/usr/local/bin/mmdc"  # Mock path
            }
        }
        
        config_file = temp_mermaid_dir.parent / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)
            
        return MCPConfig(config_file=config_file)
    
    @pytest.fixture
    def sample_templates(self, temp_mermaid_dir):
        """Create sample mermaid templates."""
        templates = [
            {
                "name": "simple-flowchart",
                "type": "flowchart",
                "content": "flowchart TD\n    A[{start}] --> B[{process}]\n    B --> C[{end}]",
                "variables": {
                    "start": "Start",
                    "process": "Process",
                    "end": "End"
                }
            },
            {
                "name": "class-diagram",
                "type": "class",
                "content": "classDiagram\n    class {class1} {\n        +{attribute1}\n        +{method1}()\n    }\n    class {class2} {\n        +{attribute2}\n        +{method2}()\n    }\n    {class1} --> {class2}",
                "variables": {
                    "class1": "ClassA",
                    "attribute1": "attributeA",
                    "method1": "methodA",
                    "class2": "ClassB",
                    "attribute2": "attributeB",
                    "method2": "methodB"
                }
            }
        ]
        
        # Write templates to files
        for template in templates:
            template_file = temp_mermaid_dir / "templates" / f"{template['name']}.json"
            with open(template_file, "w") as f:
                json.dump(template, f)
                
        return templates
    
    @pytest.mark.asyncio
    async def test_mermaid_generator_initialization(self, config, sample_templates):
        """Test that the mermaid generator initializes properly."""
        generator = MermaidGenerator(config)
        await generator.initialize()
        
        # Check if templates were loaded
        assert "simple-flowchart" in generator.templates
        assert "class-diagram" in generator.templates
        
    @pytest.mark.asyncio
    async def test_flowchart_generation(self, config):
        """Test flowchart generation."""
        generator = MermaidGenerator(config)
        await generator.initialize()
        
        nodes = [
            {"id": "A", "label": "Start"},
            {"id": "B", "label": "Process"},
            {"id": "C", "label": "End"}
        ]
        
        edges = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"}
        ]
        
        diagram = generator.generate_flowchart(nodes, edges)
        
        # Check basic structure
        assert "flowchart" in diagram
        assert "A[Start]" in diagram
        assert "B[Process]" in diagram
        assert "C[End]" in diagram
        assert "A --> B" in diagram
        assert "B --> C" in diagram
        
    @pytest.mark.asyncio
    async def test_class_diagram_generation(self, config):
        """Test class diagram generation."""
        generator = MermaidGenerator(config)
        await generator.initialize()
        
        classes = [
            {
                "name": "User",
                "properties": [
                    {"name": "id", "type": "int", "visibility": "+"},
                    {"name": "name", "type": "string", "visibility": "+"}
                ],
                "methods": [
                    {"name": "login", "params": "password", "return": "bool", "visibility": "+"},
                    {"name": "logout", "params": "", "return": "void", "visibility": "+"}
                ]
            },
            {
                "name": "Admin",
                "properties": [
                    {"name": "role", "type": "string", "visibility": "+"}
                ],
                "methods": [
                    {"name": "manageUsers", "params": "", "return": "void", "visibility": "+"}
                ]
            }
        ]
        
        relationships = [
            {"from": "Admin", "to": "User", "type": "--|>", "label": "extends"}
        ]
        
        diagram = generator.generate_class_diagram(classes, relationships)
        
        # Check basic structure
        assert "classDiagram" in diagram
        assert "class User" in diagram
        assert "+id: int" in diagram
        assert "+name: string" in diagram
        assert "+login(password) bool" in diagram
        assert "+logout() void" in diagram
        assert "class Admin" in diagram
        assert "+role: string" in diagram
        assert "+manageUsers() void" in diagram
        assert "Admin --|> User: extends" in diagram
        
    @pytest.mark.asyncio
    async def test_template_based_generation(self, config, sample_templates):
        """Test template-based diagram generation."""
        generator = MermaidGenerator(config)
        await generator.initialize()
        
        variables = {
            "start": "Begin",
            "process": "Transform",
            "end": "Finish"
        }
        
        diagram = generator.generate_from_template("simple-flowchart", variables)
        
        # Check variable substitution
        assert "A[Begin]" in diagram
        assert "B[Transform]" in diagram
        assert "C[Finish]" in diagram
        
    @pytest.mark.asyncio
    async def test_renderer_initialization(self, config, monkeypatch):
        """Test renderer initialization with a mock CLI path."""
        # Mock the existence check for the CLI
        def mock_exists(path):
            return True
            
        monkeypatch.setattr(Path, "exists", mock_exists)
        
        renderer = MermaidRenderer(config)
        await renderer.initialize()
        
        # Check if output directory was created
        assert (Path(config.mermaid_output_dir)).exists()
        
    @pytest.mark.asyncio
    async def test_renderer_render_to_file(self, config, monkeypatch):
        """Test rendering diagram to a file."""
        # Mock the subprocess call
        async def mock_run_command(*args, **kwargs):
            # Create a mock output file to simulate successful rendering
            output_file = Path(args[0][args[0].index('-o') + 1])
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write("MOCK RENDERED CONTENT")
            return 0
            
        monkeypatch.setattr(MermaidRenderer, "_run_command", mock_run_command)
        monkeypatch.setattr(Path, "exists", lambda path: True)
        
        renderer = MermaidRenderer(config)
        await renderer.initialize()
        
        diagram = "flowchart TD\n    A[Start] --> B[Process]\n    B --> C[End]"
        output_file = await renderer.render_to_file(
            diagram, 
            "test-diagram", 
            DiagramType.FLOWCHART
        )
        
        # Check if the file was created
        assert output_file.exists()
        
        # Check content
        with open(output_file, "r") as f:
            content = f.read()
        assert "MOCK RENDERED CONTENT" in content 