"""Tests for the Mermaid diagram generation system."""

import pytest
from pathlib import Path

from mcp_project_orchestrator.mermaid import (
    MermaidGenerator,
    MermaidRenderer,
    DiagramType,
    DiagramMetadata,
)

def test_diagram_metadata():
    """Test diagram metadata creation and conversion."""
    metadata = DiagramMetadata(
        name="test-diagram",
        description="Test diagram",
        type=DiagramType.FLOWCHART,
        version="1.0.0",
        author="Test Author",
        tags=["test", "flowchart"],
    )
    
    # Test to_dict
    data = metadata.to_dict()
    assert data["name"] == "test-diagram"
    assert data["type"] == "flowchart"
    
    # Test from_dict
    new_metadata = DiagramMetadata.from_dict(data)
    assert new_metadata.name == metadata.name
    assert new_metadata.type == metadata.type

def test_mermaid_generator(mermaid_generator):
    """Test Mermaid diagram generation."""
    # Generate flowchart
    flowchart = mermaid_generator.generate_flowchart(
        nodes=[
            ("A", "Start"),
            ("B", "Process"),
            ("C", "End"),
        ],
        edges=[
            ("A", "B", ""),
            ("B", "C", ""),
        ],
    )
    assert "flowchart TD" in flowchart
    assert "A[Start]" in flowchart
    assert "B[Process]" in flowchart
    assert "C[End]" in flowchart
    assert "A --> B" in flowchart
    assert "B --> C" in flowchart
    
    # Generate sequence diagram
    sequence = mermaid_generator.generate_sequence(
        participants=["User", "System"],
        messages=[
            ("User", "System", "Request"),
            ("System", "User", "Response"),
        ],
    )
    assert "sequenceDiagram" in sequence
    assert "participant User" in sequence
    assert "participant System" in sequence
    assert "User->>System: Request" in sequence
    assert "System->>User: Response" in sequence
    
    # Generate class diagram
    class_diagram = mermaid_generator.generate_class(
        classes=[
            {
                "name": "Animal",
                "attributes": ["name: str", "age: int"],
                "methods": ["speak()", "move()"],
            },
            {
                "name": "Dog",
                "attributes": ["breed: str"],
                "methods": ["bark()"],
            },
        ],
        relationships=[
            ("Dog", "Animal", "extends"),
        ],
    )
    assert "classDiagram" in class_diagram
    assert "class Animal" in class_diagram
    assert "class Dog" in class_diagram
    assert "Dog --|> Animal" in class_diagram

def test_mermaid_renderer(mermaid_renderer, temp_dir):
    """Test Mermaid diagram rendering."""
    # Create test diagram
    diagram = """
    flowchart TD
        A[Start] --> B[Process]
        B --> C[End]
    """
    
    # Render to SVG
    svg_path = temp_dir / "test.svg"
    mermaid_renderer.render(diagram, svg_path)
    assert svg_path.exists()
    assert svg_path.stat().st_size > 0
    
    # Render to PNG
    png_path = temp_dir / "test.png"
    mermaid_renderer.render(diagram, png_path)
    assert png_path.exists()
    assert png_path.stat().st_size > 0

def test_diagram_save_load(mermaid_generator, temp_dir):
    """Test saving and loading diagrams."""
    # Create diagram
    metadata = DiagramMetadata(
        name="save-test",
        description="Save test diagram",
        type=DiagramType.FLOWCHART,
        version="1.0.0",
        author="Test Author",
        tags=["test"],
    )
    diagram = """
    flowchart TD
        A[Start] --> B[Process]
        B --> C[End]
    """
    
    # Save diagram
    diagram_dir = temp_dir / "diagrams"
    diagram_dir.mkdir(parents=True)
    diagram_file = diagram_dir / "save-test.mmd"
    mermaid_generator.save_diagram(metadata, diagram, diagram_file)
    
    # Load diagram
    loaded_metadata, loaded_diagram = mermaid_generator.load_diagram(diagram_file)
    assert loaded_metadata.name == metadata.name
    assert loaded_metadata.type == metadata.type
    assert loaded_diagram.strip() == diagram.strip()

def test_diagram_validation(mermaid_generator):
    """Test diagram validation."""
    # Valid flowchart
    valid_flowchart = """
    flowchart TD
        A[Start] --> B[Process]
        B --> C[End]
    """
    assert mermaid_generator.validate_diagram(valid_flowchart, DiagramType.FLOWCHART)
    
    # Invalid flowchart (syntax error)
    invalid_flowchart = """
    flowchart TD
        A[Start] --> B[Process
        B --> C[End]
    """
    assert not mermaid_generator.validate_diagram(invalid_flowchart, DiagramType.FLOWCHART)
    
    # Valid sequence diagram
    valid_sequence = """
    sequenceDiagram
        participant A
        participant B
        A->>B: Message
    """
    assert mermaid_generator.validate_diagram(valid_sequence, DiagramType.SEQUENCE)
    
    # Invalid sequence diagram (missing participant)
    invalid_sequence = """
    sequenceDiagram
        A->>B: Message
    """
    assert not mermaid_generator.validate_diagram(invalid_sequence, DiagramType.SEQUENCE) 