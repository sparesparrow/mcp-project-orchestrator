from mcp.server.fastmcp import FastMCP
import os
import json
from typing import List, Dict, Optional

# Load MCP configuration from JSON file
CONFIG_FILE = 'project_orchestration.json'
with open(CONFIG_FILE, 'r') as config_file:
    MCP_CONFIG = json.load(config_file)

# MCP configuration details (e.g., communication_protocol, mcp_compliance) are now available in MCP_CONFIG

# Directory for projects
PROJECTS_DIR = './projects'
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Load project templates from JSON file
with open('project_templates.json', 'r') as f:
    PROJECT_TEMPLATES = json.load(f)

# Comprehensive README template aligned with JSON requirements
README_TEMPLATE = """
# {{project_name}}

## Overview
{{project_name}} is designed to {{primary_purpose}} using {{design}} patterns, adhering to systematic approaches for maintainability and scalability.

## Architecture
### Design Patterns
{{design_patterns}}

### Software Architecture
{{software_architecture}}

### Components and Modules
{{components_section}}

### Relationships
{{relationships}}

### Interfaces
{{interfaces_section}}

### Communication Protocols
{{communication_protocols}}

### Technologies
{{technologies}}

### Dependencies
{{dependencies}}

### Commands
- **Installation**: `{{install_command}}`
- **Build**: `{{build_command}}`
- **Run**: `{{run_command}}`
- **Test**: `{{test_command}}`

## File Structure
{{project_structure}}

## Implementation Strategy
{{implementation_strategy}}

## Mermaid Diagrams
{{mermaid_diagrams}}

## Instructions for Composer Implementor Agent
{{instructions}}
"""

# Initialize MCP server
mcp = FastMCP("ProjectOrchestrator")
mcp.config = MCP_CONFIG  # attach configuration to MCP server instance

'''
MCP Project Orchestrator Server
-------------------------------
This MCP server orchestrates the creation and configuration of new software projects.
It performs the following steps:
1. Extracts key design patterns and architecture concepts from user input.
2. Selects an appropriate project template from a standardized catalogue.
3. Applies the template by creating well-structured directories and placeholder files.
4. Generates comprehensive documentation including software architecture, components, process flows, and file structures.

The server configuration is loaded from 'project_orchestration.json', which defines overall settings such as communication protocols and compliance standards.

Developers can extend or modify this orchestration process by updating the template definitions or the configuration JSON.
'''

# Tool: Analyze design patterns and architecture
@mcp.tool()
def analyze_design_patterns(idea: str) -> Dict[str, List[str]]:
    """Analyze the user's idea to identify design patterns and architecture concepts."""
    idea_lower = idea.lower()
    patterns = []
    architectures = []

    keyword_map = {
        "microservices": ("Microservices Architecture", "Distributed System"),
        "event": ("Event-Driven Architecture", "Asynchronous Processing"),
        "async": ("Event-Driven Architecture", "Asynchronous Processing"),
        "data": ("Repository Pattern", "Layered Architecture"),
        "repository": ("Repository Pattern", "Layered Architecture"),
        "cqrs": ("CQRS", "Event Sourcing"),
        "client": ("Client-Server", "Request-Response"),
        "server": ("Client-Server", "Request-Response"),
        "modular": ("Modular Monolith", "Monolithic Architecture"),
        "serverless": ("Serverless Architecture", "Function-as-a-Service"),
        "bridge": ("Bridge Pattern", "Abstraction Separation"),
        "composite": ("Composite Pattern", "Tree Structure"),
        "flyweight": ("Flyweight Pattern", "Memory Optimization"),
        "strategy": ("Strategy Pattern", "Behavioral Flexibility"),
        "template": ("Template Method Pattern", "Algorithm Skeleton"),
        "visitor": ("Visitor Pattern", "Operation Separation")
    }

    for keyword, (pattern, arch) in keyword_map.items():
        if keyword in idea_lower:
            if pattern not in patterns:
                patterns.append(pattern)
            if arch not in architectures:
                architectures.append(arch)

    if not patterns:
        patterns.append("Modular Monolith")
        architectures.append("Monolithic Architecture")

    return {"design_patterns": patterns, "architectures": architectures}

# Tool: Generate Mermaid diagrams (aligned with JSON's MermaidTool)
@mcp.tool()
def mermaid_tool(diagram_planning: str, template_name: Optional[str] = None) -> str:
    """Generate Mermaid diagrams for visualization based on planning."""
    planning_lower = diagram_planning.lower()
    if "architecture" in planning_lower:
        if template_name and "Microservices" in template_name:
            return (
                "```mermaid\n"
                "graph TD\n"
                "    A[API Gateway] --> B[UserService]\n"
                "    A --> C[OrderService]\n"
                "    B --> D[UserDB]\n"
                "    C --> E[OrderDB]\n"
                "    B --> F[MessageQueue]\n"
                "    C --> F\n"
                "```\n"
            )
        elif template_name and "EventDriven" in template_name:
            return (
                "```mermaid\n"
                "graph TD\n"
                "    A[EventProducer] --> B[EventBus]\n"
                "    B --> C[EventConsumer]\n"
                "    C --> D[EventStore]\n"
                "```\n"
            )
        return (
            "```mermaid\n"
            "graph TD\n"
            "    A[CoreModule] --> B[Services]\n"
            "    B --> C[Utilities]\n"
            "    A --> D[Database]\n"
            "```\n"
        )
    elif "file structure" in planning_lower:
        if template_name:
            template = next((t for t in PROJECT_TEMPLATES if t["project_name"] == template_name), None)
            if template:
                components = "\n".join([f"    E --> F{i+1}[{c['name']}]" for i, c in enumerate(template["components"])])
                return (
                    "```mermaid\n"
                    "graph TD\n"
                    "    A[ProjectRoot] --> B[src]\n"
                    "    A --> C[tests]\n"
                    "    A --> D[docs]\n"
                    "    B --> E[components]\n"
                    f"{components}\n"
                    "    B --> G[interfaces]\n"
                    "    B --> H[services]\n"
                    "    B --> I[utils]\n"
                    "```\n"
                )
        return (
            "```mermaid\n"
            "graph TD\n"
            "    A[ProjectRoot] --> B[src]\n"
            "    A --> C[tests]\n"
            "    A --> D[docs]\n"
            "    B --> E[components]\n"
            "    B --> F[interfaces]\n"
            "    B --> G[services]\n"
            "    B --> H[utils]\n"
            "```\n"
        )
    elif "process flow" in planning_lower:
        return (
            "```mermaid\n"
            "sequenceDiagram\n"
            "    participant U as User\n"
            "    participant S as System\n"
            "    U->>S: Initiate Action\n"
            "    S-->>U: Process Result\n"
            "```\n"
        )
    return "```mermaid\n%% Placeholder diagram\n```"

# Tool: Apply project template
@mcp.tool()
def apply_project_template(template_name: str, project_name: str, user_idea: str, design_info: Dict[str, List[str]]) -> str:
    """Apply a template and create comprehensive documentation."""
    template = next((t for t in PROJECT_TEMPLATES if t["project_name"] == template_name), None)
    if not template:
        return f"Error: Template '{template_name}' not found."

    project_path = os.path.join(PROJECTS_DIR, project_name)
    if os.path.exists(project_path):
        return f"Error: Project '{project_name}' already exists."

    # Step 5: Prepare detailed file structure
    os.makedirs(os.path.join(project_path, "src", "components"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "src", "interfaces"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "src", "services"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "src", "utils"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "tests"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "docs"), exist_ok=True)

    # Generate component files with consistent names and TODOs
    components_section = ""
    interfaces_section = ""
    relationships = ""
    communication_protocols = "REST API, Message Queues" if "Microservices" in template_name else "Internal Function Calls"

    for i, component in enumerate(template["components"]):
        name = component["name"]
        # Interface
        interface_file = f"i_{name.lower()}.py"
        with open(os.path.join(project_path, "src", "interfaces", interface_file), "w") as f:
            f.write(f"# TODO: Define interface methods for {name}\nclass I{name}:\n    pass\n")
        # Implementation
        impl_file = f"{name.lower()}.py"
        with open(os.path.join(project_path, "src", "components", impl_file), "w") as f:
            f.write(f"# TODO: Implement {name} logic\nclass {name}:\n    pass\n")
        # Service (if applicable)
        service_file = f"{name.lower()}_service.py"
        with open(os.path.join(project_path, "src", "services", service_file), "w") as f:
            f.write(f"# TODO: Implement service logic for {name}\n")
        # Test
        test_file = f"test_{name.lower()}.py"
        with open(os.path.join(project_path, "tests", test_file), "w") as f:
            f.write(f"# TODO: Write unit tests for {name}\n")

        components_section += (
            f"- **{name}**: {component.get('description', 'TBD')}\n"
            f"  - Interface: [{interface_file}](./src/interfaces/{interface_file})\n"
            f"  - Implementation: [{impl_file}](./src/components/{impl_file})\n"
            f"  - Service: [{service_file}](./src/services/{service_file})\n"
            f"  - Tests: [{test_file}](./tests/{test_file})\n"
        )
        interfaces_section += f"class I{name}:\n    # TODO: Define {name} methods\n    pass\n\n"
        if i > 0:
            relationships += f"- {template['components'][i-1]['name']} interacts with {name} via {communication_protocols}\n"

    # Step 4: Comprehensive documentation
    design_patterns = "- " + "\n- ".join(design_info["design_patterns"])
    software_architecture = "- " + "\n- ".join(design_info["architectures"])
    technologies = "Python, Flask, Docker, Kafka" if "Microservices" in template_name else "Python, Django"
    dependencies = "requests, pytest, docker, confluent-kafka" if "Microservices" in template_name else "django, pytest"
    install_command = "pip install -r requirements.txt"
    build_command = "docker build ." if "Microservices" in template_name else "python manage.py migrate"
    run_command = "docker-compose up" if "Microservices" in template_name else "python manage.py runserver"
    test_command = "pytest"

    # File structure visualization
    project_structure = mermaid_tool("file structure", template_name)

    # Step 6: Implementation strategy
    impl_order = "\n".join([f"{i+1}. src/components/{c['name'].lower()}.py" for i, c in enumerate(template["components"])])
    implementation_strategy = (
        f"### File Implementation Order\n{impl_order}\n"
        "### Testing Strategies\n- Unit Tests: Use pytest for component-level testing.\n- Integration Tests: Verify inter-component interactions.\n"
        f"### Build and Deployment\n- Build: `{build_command}`\n- Deploy: Use Docker containers or a cloud platform like AWS.\n"
    )

    # Mermaid diagrams
    mermaid_diagrams = (
        f"### Architecture Diagram\n{mermaid_tool('architecture', template_name)}\n"
        f"### File Structure\n{project_structure}\n"
        f"### Process Flow\n{mermaid_tool('process flow', template_name)}"
    )

    # Instructions for the composer implementor agent
    instructions = (
        "1. Refine the generated documentation in README.md.\n"
        "2. Implement components starting with core logic in src/components/.\n"
        "3. Use mermaid_tool for additional visualizations (e.g., `mermaid_tool 'detailed process flow'`).\n"
        "4. Follow the implementation strategy and test using provided commands."
    )

    # Substitutions for README
    substitutions = {
        "project_name": project_name,
        "design": ", ".join(design_info["design_patterns"]),
        "primary_purpose": template["description"].split(".")[0],
        "design_patterns": design_patterns,
        "software_architecture": software_architecture,
        "components_section": components_section,
        "relationships": relationships if relationships else "TBD - Define inter-component relationships",
        "interfaces_section": interfaces_section,
        "communication_protocols": communication_protocols,
        "technologies": technologies,
        "dependencies": dependencies,
        "install_command": install_command,
        "build_command": build_command,
        "run_command": run_command,
        "test_command": test_command,
        "project_structure": project_structure,
        "implementation_strategy": implementation_strategy,
        "mermaid_diagrams": mermaid_diagrams,
        "instructions": instructions
    }

    # Generate README
    readme_content = README_TEMPLATE
    for key, value in substitutions.items():
        readme_content = readme_content.replace("{{" + key + "}}", value)
    with open(os.path.join(project_path, "README.md"), "w") as f:
        f.write(readme_content)

    return f"Project '{project_name}' created successfully at '{project_path}'."

# Helper: Select template
def select_template(idea: str, design_info: Dict[str, List[str]]) -> str:
    """Select a project template based on design patterns and architectures."""
    idea_lower = idea.lower()
    patterns = design_info["design_patterns"]
    template_map = {
        "Microservices Architecture": "MicroservicesArchitectureProject",
        "Event-Driven Architecture": "EventDrivenArchitectureProject",
        "Repository Pattern": "RepositoryPatternProject",
        "CQRS": "CQRSProject",
        "Client-Server": "ClientServerProject",
        "Modular Monolith": "ModularMonolithProject",
        "Serverless Architecture": "ServerlessFunctionProject",
        "Bridge Pattern": "BridgeProject",
        "Composite Pattern": "CompositeProject",
        "Flyweight Pattern": "FlyweightProject",
        "Strategy Pattern": "StrategyProject",
        "Template Method Pattern": "TemplateMethodProject",
        "Visitor Pattern": "VisitorProject"
    }
    for pattern in patterns:
        if pattern in template_map:
            return template_map[pattern]
    return "ModularMonolithProject"  # Default

# Tool: Orchestrate project setup
@mcp.tool()
def orchestrate_new_project(user_idea: str) -> str:
    """Orchestrate the setup of a new software project from the user's idea."""
    # Step 1: Information Extraction
    design_info = analyze_design_patterns(user_idea)

    # Step 2: Design Patterns & Architecture Identification (handled by analyze_design_patterns)

    # Step 3: Project Template Application
    template_name = select_template(user_idea, design_info)
    project_name = user_idea.lower().replace(" ", "_")[:20]

    # Steps 4-6: Apply template, generate documentation, prepare file structure, and define strategy
    result = apply_project_template(template_name, project_name, user_idea, design_info)
    if "Error" in result:
        return result

    return (
        f"Project '{project_name}' has been initialized with template '{template_name}'.\n"
        f"Design Patterns Identified: {', '.join(design_info['design_patterns'])}\n"
        f"Architecture Concepts: {', '.join(design_info['architectures'])}\n"
        "Next Steps: Review the generated README.md at '{project_path}/README.md' for detailed documentation and instructions."
    )

# Run the server
if __name__ == "__main__":
    mcp.run()