from conan import ConanFile
from conan.tools.files import copy, save
import os


class MCPProjectOrchestratorConan(ConanFile):
    name = "mcp-project-orchestrator"
    version = "0.1.0"
    license = "MIT"
    url = "https://github.com/sparesparrow/mcp-project-orchestrator"
    description = (
        "Main Conan manager and Python environment source for orchestrating MCP development flow."
    )
    topics = ("mcp", "orchestrator", "conan", "python", "templates", "prompts", "mermaid")

    # Pure Python application; no C/C++ settings required
    settings = None
    package_type = "application"

    exports_sources = (
        "src/*",
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "project_orchestration.json",
        "project_templates.json",
        "component_templates.json",
        "config/*",
        "data/*",
        "docs/*",
    )

    def package(self):
        """Package the Python sources and supporting resources.

        We ship the source tree under a 'python' folder and expose it via
        PYTHONPATH using the run environment so consumers can import the
        package or execute the CLI through the provided launcher script.
        """
        # Licenses and docs
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "README.md", dst=os.path.join(self.package_folder, "res"), src=self.source_folder)
        copy(self, "docs/*", dst=os.path.join(self.package_folder, "res", "docs"), src=self.source_folder)

        # Python sources
        copy(self, "src/*", dst=os.path.join(self.package_folder, "python"), src=self.source_folder)

        # Configuration and data assets used at runtime
        copy(self, "project_orchestration.json", dst=os.path.join(self.package_folder, "assets"), src=self.source_folder)
        copy(self, "project_templates.json", dst=os.path.join(self.package_folder, "assets"), src=self.source_folder)
        copy(self, "component_templates.json", dst=os.path.join(self.package_folder, "assets"), src=self.source_folder)
        copy(self, "config/*", dst=os.path.join(self.package_folder, "assets", "config"), src=self.source_folder)
        copy(self, "data/*", dst=os.path.join(self.package_folder, "assets", "data"), src=self.source_folder)

        # Simple launcher script to run the server via CLI
        bin_dir = os.path.join(self.package_folder, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        launcher = """#!/usr/bin/env bash
set -euo pipefail
exec python -m mcp_project_orchestrator.fastmcp "$@"
"""
        save(self, os.path.join(bin_dir, "mcp-orchestrator"), launcher)
        os.chmod(os.path.join(bin_dir, "mcp-orchestrator"), 0o755)

    def package_info(self):
        """Expose run-time environment so consumers can import and run tools.

        - Adds the packaged sources to PYTHONPATH
        - Adds the 'bin' directory to PATH for the 'mcp-orchestrator' launcher
        """
        pythonpath = os.path.join(self.package_folder, "python")
        bindir = os.path.join(self.package_folder, "bin")

        # Make available in consumers' run environment when using VirtualRunEnv
        self.runenv_info.append_path("PYTHONPATH", pythonpath)
        self.runenv_info.append_path("PATH", bindir)

