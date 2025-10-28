"""Prompt version implementation for MCP Project Orchestrator.

This module provides the PromptVersion class that handles version information
for prompts, following semantic versioning principles.
"""

from typing import Dict, Any


class PromptVersion:
    """Class representing a prompt version."""

    def __init__(self, major: int = 1, minor: int = 0, patch: int = 0):
        """Initialize prompt version.

        Args:
            major: Major version number
            minor: Minor version number
            patch: Patch version number
        """
        self.major = major
        self.minor = minor
        self.patch = patch

    def bump_major(self) -> None:
        """Bump major version number.

        This resets minor and patch numbers to 0.
        """
        self.major += 1
        self.minor = 0
        self.patch = 0

    def bump_minor(self) -> None:
        """Bump minor version number.

        This resets patch number to 0.
        """
        self.minor += 1
        self.patch = 0

    def bump_patch(self) -> None:
        """Bump patch version number."""
        self.patch += 1

    def is_compatible_with(self, other: "PromptVersion") -> bool:
        """Check if this version is compatible with another version.

        Compatible versions have the same major version number.

        Args:
            other: Version to compare with

        Returns:
            bool: True if versions are compatible
        """
        return self.major == other.major

    def is_newer_than(self, other: "PromptVersion") -> bool:
        """Check if this version is newer than another version.

        Args:
            other: Version to compare with

        Returns:
            bool: True if this version is newer
        """
        if self.major != other.major:
            return self.major > other.major
        if self.minor != other.minor:
            return self.minor > other.minor
        return self.patch > other.patch

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
        }

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            str: String representation in format 'major.minor.patch'
        """
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        """Get detailed string representation.

        Returns:
            str: Detailed string representation
        """
        return (
            f"PromptVersion(major={self.major}, "
            f"minor={self.minor}, "
            f"patch={self.patch})"
        )

    def __eq__(self, other: object) -> bool:
        """Check if versions are equal.

        Args:
            other: Version to compare with

        Returns:
            bool: True if versions are equal
        """
        if not isinstance(other, PromptVersion):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
        )

    def __lt__(self, other: "PromptVersion") -> bool:
        """Check if this version is less than another version.

        Args:
            other: Version to compare with

        Returns:
            bool: True if this version is less than other
        """
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch

    def __le__(self, other: "PromptVersion") -> bool:
        """Check if this version is less than or equal to another version.

        Args:
            other: Version to compare with

        Returns:
            bool: True if this version is less than or equal to other
        """
        return self < other or self == other

    def __gt__(self, other: "PromptVersion") -> bool:
        """Check if this version is greater than another version.

        Args:
            other: Version to compare with

        Returns:
            bool: True if this version is greater than other
        """
        return not (self <= other)

    def __ge__(self, other: "PromptVersion") -> bool:
        """Check if this version is greater than or equal to another version.

        Args:
            other: Version to compare with

        Returns:
            bool: True if this version is greater than or equal to other
        """
        return not (self < other) 