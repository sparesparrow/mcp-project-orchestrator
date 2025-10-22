#!/usr/bin/env python3
"""
OpenSSL Tools Orchestration Main Entry Point.

This module provides the main entry point for OpenSSL tools orchestration,
integrating all the Skills-enabled capabilities for comprehensive project management.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

from .skills_enabled_mcp import SkillsEnabledMCPServer
from .openssl_tools_orchestration import (
    OpenSSLToolsOrchestrator,
    OpenSSLProjectContext,
    OpenSSLProjectType,
    BuildPlatform,
    CursorExecutionMode
)

logger = logging.getLogger(__name__)

class OpenSSLOrchestrationMain:
    """
    Main orchestration class for OpenSSL tools development.
    
    This class integrates all the Skills-enabled capabilities to provide
    comprehensive orchestration for OpenSSL projects.
    """
    
    def __init__(self):
        self.mcp_server = SkillsEnabledMCPServer("OpenSSL Tools Orchestrator")
        self.openssl_orchestrator = OpenSSLToolsOrchestrator()
        
        # Register OpenSSL-specific tools
        self._register_openssl_tools()
        
        logger.info("Initialized OpenSSL Orchestration Main")
    
    def _register_openssl_tools(self) -> None:
        """Register OpenSSL-specific MCP tools."""
        
        @self.mcp_server.tool()
        async def orchestrate_openssl_tools_project(
            project_type: str,
            repository_url: str,
            target_platforms: List[str],
            fips_required: bool = False,
            ci_cd_enabled: bool = True,
            testing_framework: str = "pytest",
            execution_mode: str = "autonomous"
        ) -> Dict[str, Any]:
            """Orchestrate complete OpenSSL tools project setup."""
            
            try:
                # Create project context
                context = OpenSSLProjectContext(
                    project_type=OpenSSLProjectType(project_type),
                    repository_url=repository_url,
                    target_platforms=[BuildPlatform(p) for p in target_platforms],
                    fips_required=fips_required,
                    ci_cd_enabled=ci_cd_enabled,
                    testing_framework=testing_framework,
                    build_tools=["cmake", "make", "gcc", "clang"],
                    dependencies=["openssl", "zlib", "libssl-dev"]
                )
                
                # Execute orchestration
                result = await self.openssl_orchestrator.orchestrate_openssl_tools_project(
                    context,
                    CursorExecutionMode(execution_mode)
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in OpenSSL tools orchestration: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "project_path": None,
                    "skills_applied": [],
                    "workflows_generated": 0,
                    "build_configs_generated": 0,
                    "testing_framework": {"success": False},
                    "fips_framework": {"success": False},
                    "cursor_orchestration": False,
                    "execution_time": 0.0,
                    "artifacts": {}
                }
        
        @self.mcp_server.tool()
        async def create_openssl_ci_workflow(
            project_name: str,
            platforms: List[str],
            fips_enabled: bool = False,
            triggers: List[str] = None
        ) -> Dict[str, Any]:
            """Create GitHub Actions CI workflow for OpenSSL project."""
            
            try:
                from .openssl_tools_orchestration import OpenSSLWorkflowConfig, WorkflowTrigger
                
                # Create workflow configuration
                workflow_config = OpenSSLWorkflowConfig(
                    name=f"{project_name} CI/CD",
                    description=f"CI/CD pipeline for {project_name}",
                    triggers=[WorkflowTrigger(t) for t in (triggers or ["push", "pull_request"])],
                    platforms=[BuildPlatform(p) for p in platforms],
                    steps=[
                        {"name": "Checkout", "uses": "actions/checkout@v4"},
                        {"name": "Setup Python", "uses": "actions/setup-python@v4"},
                        {"name": "Install Dependencies", "run": "pip install -r requirements.txt"},
                        {"name": "Run Tests", "run": "pytest"},
                        {"name": "Build", "run": "./scripts/build.sh"}
                    ]
                )
                
                # Generate workflow YAML
                workflow_generator = self.openssl_orchestrator.workflow_generator
                yaml_content = await workflow_generator.generate_workflow_yaml(workflow_config)
                
                return {
                    "success": True,
                    "workflow_yaml": yaml_content,
                    "workflow_name": workflow_config.name,
                    "platforms": platforms,
                    "triggers": triggers or ["push", "pull_request"]
                }
                
            except Exception as e:
                logger.error(f"Error creating CI workflow: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "workflow_yaml": "",
                    "workflow_name": "",
                    "platforms": [],
                    "triggers": []
                }
        
        @self.mcp_server.tool()
        async def validate_openssl_fips_compliance(
            code_changes: List[str],
            fips_context: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Validate OpenSSL code against FIPS 140-3 requirements."""
            
            try:
                # Use the FIPS compliance validator
                fips_validator = self.openssl_orchestrator.fips_validator
                validation_result = await fips_validator.validate_crypto_changes(
                    code_changes, fips_context
                )
                
                return {
                    "success": True,
                    "compliant": validation_result.compliant,
                    "violations": [
                        {
                            "type": v.violation_type.value,
                            "severity": v.severity,
                            "message": v.message,
                            "line_number": v.line_number,
                            "fix_suggestion": v.fix_suggestion
                        }
                        for v in validation_result.violations
                    ],
                    "recommendations": validation_result.recommendations,
                    "security_assessment": validation_result.security_assessment,
                    "certification_impact": validation_result.certification_impact,
                    "execution_time": validation_result.execution_time
                }
                
            except Exception as e:
                logger.error(f"Error in FIPS compliance validation: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "compliant": False,
                    "violations": [],
                    "recommendations": [],
                    "security_assessment": {},
                    "certification_impact": "unknown",
                    "execution_time": 0.0
                }
        
        @self.mcp_server.tool()
        async def build_openssl_for_platforms(
            platforms: List[str],
            fips_enabled: bool = False
        ) -> Dict[str, Any]:
            """Build OpenSSL for multiple platforms."""
            
            try:
                from .openssl_tools_orchestration import OpenSSLBuildManager, BuildPlatform
                
                build_manager = OpenSSLBuildManager()
                build_results = []
                
                for platform_str in platforms:
                    platform = BuildPlatform(platform_str)
                    result = await build_manager.build_openssl(platform, fips_enabled)
                    
                    build_results.append({
                        "platform": platform.value,
                        "success": result.success,
                        "build_time": result.build_time,
                        "artifacts": result.artifacts,
                        "test_results": result.test_results,
                        "fips_validation": result.fips_validation,
                        "security_scan": result.security_scan,
                        "errors": result.errors,
                        "warnings": result.warnings
                    })
                
                # Calculate overall success
                all_successful = all(result["success"] for result in build_results)
                total_build_time = sum(result["build_time"] for result in build_results)
                
                return {
                    "success": all_successful,
                    "platforms": platforms,
                    "build_results": build_results,
                    "total_build_time": total_build_time,
                    "fips_enabled": fips_enabled
                }
                
            except Exception as e:
                logger.error(f"Error building OpenSSL: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "platforms": platforms,
                    "build_results": [],
                    "total_build_time": 0.0,
                    "fips_enabled": fips_enabled
                }
        
        @self.mcp_server.tool()
        async def create_openssl_release(
            version: str,
            platforms: List[str],
            fips_enabled: bool = False
        ) -> Dict[str, Any]:
            """Create OpenSSL release for multiple platforms."""
            
            try:
                from .openssl_tools_orchestration import OpenSSLReleaseManager, BuildPlatform
                
                release_manager = OpenSSLReleaseManager()
                platform_enums = [BuildPlatform(p) for p in platforms]
                
                result = await release_manager.create_release(
                    version, platform_enums, fips_enabled
                )
                
                return {
                    "success": result["success"],
                    "version": result["version"],
                    "platforms": result["platforms"],
                    "artifacts": result["artifacts"],
                    "build_results": result["build_results"],
                    "error": result.get("error")
                }
                
            except Exception as e:
                logger.error(f"Error creating OpenSSL release: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "version": version,
                    "platforms": platforms,
                    "artifacts": [],
                    "build_results": []
                }
        
        @self.mcp_server.tool()
        async def get_openssl_skills_catalog() -> Dict[str, Any]:
            """Get catalog of available OpenSSL Skills."""
            
            try:
                skills_catalog = []
                
                for skill_id, skill in self.openssl_orchestrator.skills_registry.skill_index.items():
                    skills_catalog.append({
                        "skill_id": skill.skill_id,
                        "name": skill.name,
                        "description": skill.description,
                        "skill_type": skill.skill_type.value,
                        "priority": skill.priority.value,
                        "triggers": skill.triggers,
                        "tags": skill.tags,
                        "verification_required": skill.verification_required,
                        "auto_compose": skill.auto_compose,
                        "progressive_files": skill.progressive_files
                    })
                
                return {
                    "success": True,
                    "skills": skills_catalog,
                    "total_count": len(skills_catalog),
                    "categories": {
                        "orchestration": len([s for s in skills_catalog if s["skill_type"] == "orchestration"]),
                        "fips": len([s for s in skills_catalog if s["skill_type"] == "fips"]),
                        "testing": len([s for s in skills_catalog if s["skill_type"] == "testing"]),
                        "deployment": len([s for s in skills_catalog if s["skill_type"] == "deployment"])
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting OpenSSL skills catalog: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "skills": [],
                    "total_count": 0,
                    "categories": {}
                }
    
    async def run_server(self) -> None:
        """Run the OpenSSL orchestration server."""
        logger.info("Starting OpenSSL Tools Orchestration Server")
        
        try:
            # Start the MCP server
            await self.mcp_server.run()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Error running server: {e}")
            raise
        finally:
            logger.info("OpenSSL Tools Orchestration Server stopped")

def main() -> None:
    """Main entry point for OpenSSL orchestration."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    # Create and run the orchestration main
    orchestration_main = OpenSSLOrchestrationMain()
    
    try:
        asyncio.run(orchestration_main.run_server())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()