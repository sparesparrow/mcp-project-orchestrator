# MCP Project Orchestrator

[![CI/CD](https://github.com/yourusername/mcp-project-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/mcp-project-orchestrator/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/mcp-project-orchestrator/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/mcp-project-orchestrator)
[![PyPI version](https://badge.fury.io/py/mcp-project-orchestrator.svg)](https://badge.fury.io/py/mcp-project-orchestrator)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive project orchestration tool for managing Model Context Protocol (MCP) projects, templates, prompts, and Mermaid diagrams.

## Features

- **Template Management**
  - Project templates for quick project setup
  - Component templates for modular development
  - Variable substitution and validation
  - Template discovery and versioning

- **Prompt Management**
  - System and user prompt templates
  - Variable substitution
  - Prompt categorization and versioning
  - Easy prompt discovery and reuse

- **Mermaid Diagram Generation**
  - Flowchart generation
  - Sequence diagram generation
  - Class diagram generation
  - SVG and PNG rendering
  - Diagram validation

## Installation

```bash
pip install mcp-project-orchestrator
```

Or with Poetry:

```bash
poetry add mcp-project-orchestrator
```

## Quick Start

### Project Templates

```python
from mcp_project_orchestrator.templates import TemplateManager

# Initialize template manager
manager = TemplateManager("path/to/templates")

# List available templates
templates = manager.list_templates()
print(templates)

# Apply a project template
manager.apply_template("fastapi-project", {
    "project_name": "my-api",
    "project_description": "My FastAPI project",
    "author_name": "John Doe",
    "author_email": "john@example.com"
})
```

### Prompt Management

```python
from mcp_project_orchestrator.prompts import PromptManager

# Initialize prompt manager
manager = PromptManager("path/to/prompts")

# List available prompts
prompts = manager.list_prompts()
print(prompts)

# Render a prompt with variables
rendered = manager.render_prompt("system-prompt", {
    "name": "User",
    "project": "MCP"
})
print(rendered)
```

### Mermaid Diagrams

```python
from mcp_project_orchestrator.mermaid import MermaidGenerator, MermaidRenderer

# Initialize generators
generator = MermaidGenerator()
renderer = MermaidRenderer()

# Generate a flowchart
flowchart = generator.generate_flowchart(
    nodes=[
        ("A", "Start"),
        ("B", "Process"),
        ("C", "End")
    ],
    edges=[
        ("A", "B", ""),
        ("B", "C", "")
    ]
)

# Render to SVG
renderer.render(flowchart, "flowchart.svg")
```

## Project Structure

```
mcp-project-orchestrator/
├── src/
│   └── mcp_project_orchestrator/
│       ├── templates/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── project.py
│       │   ├── component.py
│       │   └── manager.py
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── template.py
│       │   └── manager.py
│       └── mermaid/
│           ├── __init__.py
│           ├── generator.py
│           └── renderer.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_templates.py
│   ├── test_prompts.py
│   └── test_mermaid.py
├── docs/
├── examples/
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
├── Containerfile
└── README.md
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcp-project-orchestrator.git
cd mcp-project-orchestrator
```

2. Install dependencies:
```bash
poetry install
```

3. Run tests:
```bash
poetry run pytest
```

4. Run linting:
```bash
poetry run ruff check .
poetry run mypy src/mcp_project_orchestrator
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Model Context Protocol](https://github.com/yourusername/model-context-protocol) - The foundation for this project
- [Mermaid](https://mermaid-js.github.io/mermaid/) - For diagram generation
- [Poetry](https://python-poetry.org/) - For dependency management
- [Ruff](https://github.com/astral-sh/ruff) - For linting
- [mypy](https://mypy.readthedocs.io/) - For type checking