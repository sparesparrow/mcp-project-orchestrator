# Using MCP Project Orchestrator with Conan

## Package coordinates

- Reference: `mcp-project-orchestrator/0.1.0@sparesparrow/stable`
- Type: application (pure Python)

## Consuming from ai-servis

In `conanfile.py`:

```python
class AIServis(ConanFile):
    settings = None

    def requirements(self):
        self.requires("mcp-project-orchestrator/0.1.0@sparesparrow/stable")
```

Then:

```bash
conan install . -g VirtualRunEnv
source conanrun.sh  # or ./conanrun.ps1 on Windows
mcp-orchestrator --help
python -c "import mcp_project_orchestrator; print(mcp_project_orchestrator.__version__)"
```

The package exports the `bin/mcp-orchestrator` launcher and sets `PYTHONPATH` via the `VirtualRunEnv` generator.
