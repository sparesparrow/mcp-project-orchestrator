# Integrating Mermaid Server with Other MCP Servers

The Mermaid MCP Server can be integrated with other MCP servers to create powerful workflows. Here are some common integration patterns:

## GitHub Integration

Use the GitHub MCP Server with Mermaid to commit generated diagrams to repositories:

```python
# Example workflow: Generate a diagram and commit it to GitHub
# 1. Generate a diagram with Mermaid
diagram = mermaid_server.generate_diagram(
    "Create a sequence diagram for API authentication flow", 
    theme="dark"
)

# 2. Commit the diagram to GitHub
github_server.create_or_update_file(
    owner="your-username",
    repo="your-repo",
    path="docs/diagrams/authentication-flow.mmd",
    content=diagram,
    message="Add authentication flow diagram",
    branch="main"
)
```

## Database Integration

Store and retrieve diagrams using the PostgreSQL or SQLite MCP Server:

```python
# Example workflow: Store a diagram in a database
# 1. Generate a diagram with Mermaid
diagram = mermaid_server.generate_diagram(
    "Create an ER diagram for a social media database", 
    theme="vibrant"
)

# 2. Store the diagram in a database
postgres_server.execute_query(
    query="INSERT INTO diagrams (name, content, created_at) VALUES ($1, $2, NOW())",
    parameters=["social_media_er_diagram", diagram]
)
```

## Memory Integration

Use the Memory MCP Server to remember your commonly used diagrams:

```python
# Example workflow: Save a diagram to memory
# 1. Generate a diagram with Mermaid
diagram = mermaid_server.generate_diagram(
    "Create a flowchart for user onboarding", 
    theme="pastel"
)

# 2. Store the diagram in memory
memory_server.add_memory(
    content=f"User onboarding flowchart: ```mermaid\n{diagram}\n```",
    metadata={
        "type": "diagram",
        "diagram_type": "flowchart",
        "topic": "user_onboarding",
        "theme": "pastel"
    }
)
```

## Slack Integration

Share diagrams with your team via Slack:

```python
# Example workflow: Generate a diagram and post it to Slack
# 1. Generate a diagram with Mermaid
diagram = mermaid_server.generate_diagram(
    "Create a class diagram for our e-commerce application", 
    theme="default"
)

# 2. Generate an SVG preview
svg_base64 = mermaid_server.preview_diagram(diagram)

# 3. Post to Slack with the preview
slack_server.post_message(
    channel="#engineering",
    text="Here's the class diagram for our e-commerce app:",
    blocks=[
        {
            "type": "image",
            "title": {
                "type": "plain_text",
                "text": "E-commerce Class Diagram"
            },
            "image_url": f"data:image/svg+xml;base64,{svg_base64}",
            "alt_text": "Class Diagram"
        }
    ]
)
```

## File System Integration

Save diagrams and SVG previews to the filesystem:

```python
# Example workflow: Generate a diagram and save it to the filesystem
# 1. Generate a diagram with Mermaid
diagram = mermaid_server.generate_diagram(
    "Create a network diagram for our infrastructure", 
    theme="dark"
)

# 2. Generate an SVG preview
svg_base64 = mermaid_server.preview_diagram(diagram)
svg_bytes = base64.b64decode(svg_base64)

# 3. Save to filesystem
filesystem_server.write_file(
    path="diagrams/network_diagram.mmd",
    content=diagram
)

filesystem_server.write_file(
    path="diagrams/network_diagram.svg",
    content=svg_bytes,
    mode="binary"
)
```

## Orchestrator Integration

Use an orchestrator to coordinate complex workflows:

```python
# Example workflow: Orchestrate a complex diagramming process
orchestrator_server.create_workflow(
    name="diagram_workflow",
    steps=[
        {
            "name": "generate_diagram",
            "server": "mermaid-generator",
            "tool": "generate_diagram",
            "params": {
                "query": "Create a sequence diagram for user registration",
                "theme": "vibrant"
            },
            "output_var": "diagram"
        },
        {
            "name": "analyze_diagram",
            "server": "mermaid-generator",
            "tool": "analyze_diagram",
            "params": {
                "diagram": "$diagram"
            },
            "output_var": "analysis"
        },
        {
            "name": "modify_diagram",
            "server": "mermaid-generator",
            "tool": "modify_diagram",
            "params": {
                "diagram": "$diagram",
                "modification": "Add error handling for duplicate email",
                "theme": "vibrant"
            },
            "output_var": "improved_diagram"
        },
        {
            "name": "save_to_github",
            "server": "github",
            "tool": "create_or_update_file",
            "params": {
                "owner": "your-username",
                "repo": "your-repo",
                "path": "docs/diagrams/user_registration.mmd",
                "content": "$improved_diagram",
                "message": "Add user registration diagram with error handling",
                "branch": "main"
            }
        }
    ]
)
```

These integrations demonstrate how the Mermaid MCP Server can be part of larger workflows, combining with other servers to automate diagram creation, storage, sharing, and version control. 