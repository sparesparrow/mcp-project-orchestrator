"""
Prompts API for the MCP Project Orchestrator.

Exports expected test-facing classes:
- PromptManager, PromptTemplate, PromptVersion
"""

from .manager import PromptManager
from .template import PromptTemplate
from .version import PromptVersion

__all__ = [
    "PromptManager",
    "PromptTemplate",
    "PromptVersion",
]
