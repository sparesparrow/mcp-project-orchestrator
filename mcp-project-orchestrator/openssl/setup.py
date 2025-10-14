#!/usr/bin/env python3
"""
Setup script for mcp-project-orchestrator/openssl package.

This package provides Cursor configuration management for OpenSSL development,
similar to how Conan manages build profiles.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="mcp-project-orchestrator-openssl",
    version="0.1.0",
    author="MCP Project Orchestrator Team",
    author_email="team@mcp-project-orchestrator.org",
    description="Cursor configuration management for OpenSSL development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sparesparrow/mcp-project-orchestrator",
    project_urls={
        "Bug Reports": "https://github.com/sparesparrow/mcp-project-orchestrator/issues",
        "Source": "https://github.com/sparesparrow/mcp-project-orchestrator",
        "Documentation": "https://github.com/sparesparrow/mcp-project-orchestrator/blob/main/docs/",
    },
    packages=find_packages(),
    package_data={
        "mcp_orchestrator": [
            "cursor-rules/**/*",
            "cursor-rules/**/*.jinja2",
            "cursor-rules/**/*.md",
        ],
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mcp-orchestrator=mcp_orchestrator.cli:cli",
            "deploy-cursor=mcp_orchestrator.deploy_cursor:deploy_cursor",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Security :: Cryptography",
    ],
    keywords="openssl, cursor, ide, configuration, management, conan, build, profiles",
    zip_safe=False,
)