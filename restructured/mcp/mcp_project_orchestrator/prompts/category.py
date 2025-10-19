"""Prompt category implementation for MCP Project Orchestrator.

This module provides the PromptCategory class that handles prompt categorization
and organization.
"""

from typing import Dict, List, Any, Optional


class PromptCategory:
    """Class representing a prompt category."""

    def __init__(
        self,
        name: str,
        description: str = "",
        prompts: Optional[List[str]] = None
    ):
        """Initialize prompt category.

        Args:
            name: Category name
            description: Category description
            prompts: List of prompt names in this category
        """
        self.name = name
        self.description = description
        self.prompts = prompts or []

    def add_prompt(self, prompt_name: str) -> None:
        """Add a prompt to the category.

        Args:
            prompt_name: Name of the prompt to add
        """
        if prompt_name not in self.prompts:
            self.prompts.append(prompt_name)

    def remove_prompt(self, prompt_name: str) -> None:
        """Remove a prompt from the category.

        Args:
            prompt_name: Name of the prompt to remove
        """
        if prompt_name in self.prompts:
            self.prompts.remove(prompt_name)

    def has_prompt(self, prompt_name: str) -> bool:
        """Check if a prompt is in this category.

        Args:
            prompt_name: Name of the prompt to check

        Returns:
            bool: True if prompt is in category, False otherwise
        """
        return prompt_name in self.prompts

    def get_prompts(self) -> List[str]:
        """Get list of prompts in this category.

        Returns:
            List[str]: List of prompt names
        """
        return self.prompts.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert category to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "prompts": self.prompts,
        }

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            str: String representation
        """
        return f"{self.name} ({len(self.prompts)} prompts)"

    def __repr__(self) -> str:
        """Get detailed string representation.

        Returns:
            str: Detailed string representation
        """
        return (
            f"PromptCategory(name='{self.name}', "
            f"prompts={len(self.prompts)})"
        ) 