#!/usr/bin/env python3
"""
Cursor CLI Integration for Skills-Enabled Project Orchestration.

This module implements Cursor CLI integration with Skills-aware configuration
deployment, enabling headless orchestration and automated project management.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import shutil
import yaml

logger = logging.getLogger(__name__)

class CursorExecutionMode(Enum):
    """Cursor CLI execution modes."""
    INTERACTIVE = "interactive"
    HEADLESS = "headless"
    SUPERVISED = "supervised"
    AUTONOMOUS = "autonomous"

class CursorSessionStatus(Enum):
    """Cursor session status."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class CursorSession:
    """Represents an active Cursor CLI session."""
    session_id: str
    project_path: Path
    mode: CursorExecutionMode
    status: CursorSessionStatus
    skills_deployed: List[str] = field(default_factory=list)
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    last_activity: float = field(default_factory=lambda: asyncio.get_event_loop().time())

@dataclass
class CursorExecutionResult:
    """Result of Cursor CLI execution."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    artifacts_created: List[str] = field(default_factory=list)
    skills_activated: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class CursorCLIManager:
    """Manages Cursor CLI operations and sessions."""
    
    def __init__(self, cursor_cli_path: str = "cursor-agent"):
        self.cursor_cli_path = cursor_cli_path
        self.active_sessions: Dict[str, CursorSession] = {}
        self.skills_deployer = CursorSkillsDeployer()
        self.config_generator = CursorConfigGenerator()
        
        logger.info(f"Initialized Cursor CLI Manager with path: {cursor_cli_path}")
    
    async def create_session(
        self, 
        project_path: Path, 
        mode: CursorExecutionMode = CursorExecutionMode.INTERACTIVE
    ) -> CursorSession:
        """Create a new Cursor CLI session."""
        
        session_id = f"cursor_session_{int(asyncio.get_event_loop().time())}"
        
        session = CursorSession(
            session_id=session_id,
            project_path=project_path,
            mode=mode,
            status=CursorSessionStatus.INITIALIZING
        )
        
        self.active_sessions[session_id] = session
        
        # Initialize session
        await self._initialize_session(session)
        
        logger.info(f"Created Cursor session {session_id} for project {project_path}")
        return session
    
    async def _initialize_session(self, session: CursorSession) -> None:
        """Initialize a Cursor session."""
        try:
            # Ensure project directory exists
            session.project_path.mkdir(parents=True, exist_ok=True)
            
            # Check if Cursor CLI is available
            if not await self._check_cursor_cli_availability():
                raise RuntimeError("Cursor CLI not available")
            
            # Initialize Cursor configuration
            await self._initialize_cursor_config(session)
            
            session.status = CursorSessionStatus.ACTIVE
            session.last_activity = asyncio.get_event_loop().time()
            
        except Exception as e:
            logger.error(f"Failed to initialize Cursor session {session.session_id}: {e}")
            session.status = CursorSessionStatus.FAILED
            raise
    
    async def _check_cursor_cli_availability(self) -> bool:
        """Check if Cursor CLI is available."""
        try:
            result = await asyncio.create_subprocess_exec(
                self.cursor_cli_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return result.returncode == 0
        except Exception:
            return False
    
    async def _initialize_cursor_config(self, session: CursorSession) -> None:
        """Initialize Cursor configuration for the session."""
        cursor_dir = session.project_path / ".cursor"
        cursor_dir.mkdir(exist_ok=True)
        
        # Create basic Cursor configuration
        config = {
            "version": "1.0.0",
            "mcp_servers": [],
            "rules": [],
            "skills": [],
            "workflows": []
        }
        
        config_file = cursor_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    async def execute_command(
        self, 
        session: CursorSession, 
        command: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CursorExecutionResult:
        """Execute a command in the Cursor session."""
        
        if session.status != CursorSessionStatus.ACTIVE:
            return CursorExecutionResult(
                success=False,
                output="",
                error=f"Session {session.session_id} is not active (status: {session.status.value})"
            )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Prepare command arguments
            cmd_args = [self.cursor_cli_path]
            
            if session.mode == CursorExecutionMode.HEADLESS:
                cmd_args.append("--headless")
            
            cmd_args.extend([
                f"--project-root={session.project_path}",
                command
            ])
            
            # Add context if provided
            if context:
                context_file = session.project_path / ".cursor" / "context.json"
                with open(context_file, 'w') as f:
                    json.dump(context, f, indent=2)
                cmd_args.append(f"--context={context_file}")
            
            # Execute command
            logger.info(f"Executing Cursor command: {' '.join(cmd_args)}")
            
            result = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=session.project_path
            )
            
            stdout, stderr = await result.communicate()
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Log execution
            execution_log_entry = {
                "timestamp": asyncio.get_event_loop().time(),
                "command": command,
                "success": result.returncode == 0,
                "execution_time": execution_time,
                "output_length": len(stdout.decode()),
                "error_length": len(stderr.decode())
            }
            session.execution_log.append(execution_log_entry)
            session.last_activity = asyncio.get_event_loop().time()
            
            return CursorExecutionResult(
                success=result.returncode == 0,
                output=stdout.decode(),
                error=stderr.decode() if result.returncode != 0 else None,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error executing Cursor command: {e}")
            return CursorExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=asyncio.get_event_loop().time() - start_time
            )
    
    async def deploy_skills_to_session(
        self, 
        session: CursorSession, 
        skills_manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy Skills to a Cursor session."""
        
        try:
            # Deploy Skills resources
            skills_result = await self.skills_deployer.deploy_skills(
                session.project_path, skills_manifest
            )
            
            # Update Cursor configuration
            config_result = await self.config_generator.update_cursor_config(
                session.project_path, skills_manifest
            )
            
            # Update session
            session.skills_deployed.extend(skills_manifest.get("skills", []))
            
            return {
                "success": skills_result["success"] and config_result["success"],
                "skills_deployed": skills_result["skills_deployed"],
                "config_updated": config_result["config_updated"],
                "session_updated": True
            }
            
        except Exception as e:
            logger.error(f"Error deploying skills to session: {e}")
            return {
                "success": False,
                "error": str(e),
                "skills_deployed": [],
                "config_updated": False,
                "session_updated": False
            }
    
    async def close_session(self, session_id: str) -> bool:
        """Close a Cursor session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = CursorSessionStatus.COMPLETED
            del self.active_sessions[session_id]
            logger.info(f"Closed Cursor session {session_id}")
            return True
        return False
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a Cursor session."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return {
            "session_id": session_id,
            "project_path": str(session.project_path),
            "mode": session.mode.value,
            "status": session.status.value,
            "skills_deployed": session.skills_deployed,
            "execution_count": len(session.execution_log),
            "created_at": session.created_at,
            "last_activity": session.last_activity
        }

class CursorSkillsDeployer:
    """Deploys Agent Skills to Cursor configuration."""
    
    async def deploy_skills(
        self, 
        project_path: Path, 
        skills_manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy Skills to project directory."""
        
        try:
            skills_dir = project_path / ".cursor" / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)
            
            skills_deployed = []
            
            for skill in skills_manifest.get("skills", []):
                skill_result = await self._deploy_single_skill(skills_dir, skill)
                if skill_result["success"]:
                    skills_deployed.append(skill_result["skill_id"])
            
            return {
                "success": True,
                "skills_deployed": skills_deployed,
                "skills_dir": str(skills_dir)
            }
            
        except Exception as e:
            logger.error(f"Error deploying skills: {e}")
            return {
                "success": False,
                "error": str(e),
                "skills_deployed": []
            }
    
    async def _deploy_single_skill(self, skills_dir: Path, skill: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a single skill."""
        
        try:
            skill_id = skill.get("skill_id", "unknown")
            skill_dir = skills_dir / skill_id
            skill_dir.mkdir(exist_ok=True)
            
            # Create SKILL.md
            skill_md = skill_dir / "SKILL.md"
            skill_content = self._generate_skill_content(skill)
            skill_md.write_text(skill_content)
            
            # Create supporting files
            if "progressive_files" in skill:
                for filename, content in skill["progressive_files"].items():
                    file_path = skill_dir / filename
                    file_path.parent.mkdir(exist_ok=True)
                    file_path.write_text(content)
            
            return {
                "success": True,
                "skill_id": skill_id,
                "files_created": [str(skill_md)]
            }
            
        except Exception as e:
            logger.error(f"Error deploying skill {skill_id}: {e}")
            return {
                "success": False,
                "skill_id": skill_id,
                "error": str(e)
            }
    
    def _generate_skill_content(self, skill: Dict[str, Any]) -> str:
        """Generate SKILL.md content for a skill."""
        
        return f"""# {skill.get('name', 'Unknown Skill')}

{skill.get('description', 'No description available')}

## Triggers
{', '.join(skill.get('triggers', []))}

## Usage
This skill is automatically activated when the triggers are detected in your project context.

## Progressive Files
{self._format_progressive_files(skill.get('progressive_files', {}))}

## Configuration
- **Skill Type**: {skill.get('skill_type', 'unknown')}
- **Priority**: {skill.get('priority', 'medium')}
- **Verification Required**: {skill.get('verification_required', False)}
- **Auto Compose**: {skill.get('auto_compose', True)}
"""
    
    def _format_progressive_files(self, progressive_files: Dict[str, str]) -> str:
        """Format progressive files section."""
        if not progressive_files:
            return "No progressive files available."
        
        files_list = []
        for filename, description in progressive_files.items():
            files_list.append(f"- **{filename}**: {description}")
        
        return '\n'.join(files_list)

class CursorConfigGenerator:
    """Generates and updates Cursor configuration."""
    
    async def update_cursor_config(
        self, 
        project_path: Path, 
        skills_manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update Cursor configuration with Skills."""
        
        try:
            cursor_dir = project_path / ".cursor"
            config_file = cursor_dir / "config.json"
            
            # Load existing config
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {"version": "1.0.0", "mcp_servers": [], "rules": [], "skills": [], "workflows": []}
            
            # Update with Skills
            config["skills"] = skills_manifest.get("skills", [])
            
            # Add MCP servers for Skills
            mcp_servers = set(config.get("mcp_servers", []))
            for skill in skills_manifest.get("skills", []):
                skill_type = skill.get("skill_type", "")
                if skill_type == "fips":
                    mcp_servers.add("fips-validator-mcp")
                elif skill_type == "security":
                    mcp_servers.add("security-scanner-mcp")
                elif skill_type == "deployment":
                    mcp_servers.add("cursor-integration-mcp")
            
            config["mcp_servers"] = list(mcp_servers)
            
            # Add rules for Skills
            rules = config.get("rules", [])
            for skill in skills_manifest.get("skills", []):
                rule = {
                    "name": f"{skill.get('name', 'Unknown')} Rule",
                    "description": skill.get("description", ""),
                    "triggers": skill.get("triggers", []),
                    "enabled": True,
                    "skill_id": skill.get("skill_id", "")
                }
                rules.append(rule)
            
            config["rules"] = rules
            
            # Write updated config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return {
                "success": True,
                "config_updated": True,
                "config_file": str(config_file)
            }
            
        except Exception as e:
            logger.error(f"Error updating Cursor config: {e}")
            return {
                "success": False,
                "error": str(e),
                "config_updated": False
            }

class CursorAgentOrchestrator:
    """Orchestrates project execution using Cursor Agent CLI."""
    
    def __init__(self):
        self.cli_manager = CursorCLIManager()
        self.session_manager = CursorSessionManager()
        
    async def execute_autonomous_orchestration(
        self,
        project_path: Path,
        orchestration_plan: Dict[str, Any]
    ) -> 'OrchestrationExecutionResult':
        """Execute project orchestration using Cursor Agent CLI."""
        
        try:
            # Create Cursor session
            session = await self.cli_manager.create_session(
                project_path, 
                CursorExecutionMode.AUTONOMOUS
            )
            
            # Deploy Skills if specified
            if "skills_manifest" in orchestration_plan:
                skills_result = await self.cli_manager.deploy_skills_to_session(
                    session, orchestration_plan["skills_manifest"]
                )
                if not skills_result["success"]:
                    logger.warning(f"Skills deployment failed: {skills_result.get('error', 'Unknown error')}")
            
            # Execute orchestration phases
            results = []
            for phase in orchestration_plan.get("phases", []):
                phase_result = await self._execute_phase(session, phase)
                results.append(phase_result)
                
                # Verification loop after each phase
                if phase.get("verification_required", True):
                    verification = await self._verify_phase_completion(session, phase)
                    if not verification["success"]:
                        # Attempt recovery
                        recovery_result = await self._attempt_recovery(session, phase, verification)
                        results.append(recovery_result)
            
            # Close session
            await self.cli_manager.close_session(session.session_id)
            
            return OrchestrationExecutionResult(
                success=True,
                session_id=session.session_id,
                phases_executed=len(results),
                results=results,
                total_execution_time=sum(r.execution_time for r in results),
                skills_activated=session.skills_deployed
            )
            
        except Exception as e:
            logger.error(f"Error in autonomous orchestration: {e}")
            return OrchestrationExecutionResult(
                success=False,
                error=str(e),
                session_id=None,
                phases_executed=0,
                results=[],
                total_execution_time=0.0,
                skills_activated=[]
            )
    
    async def _execute_phase(
        self, 
        session: CursorSession, 
        phase: Dict[str, Any]
    ) -> CursorExecutionResult:
        """Execute a single orchestration phase."""
        
        phase_instruction = self._generate_phase_instruction(phase)
        
        # Add Skills context if available
        context = {}
        if "skills_context" in phase:
            context["skills"] = phase["skills_context"]
        
        return await self.cli_manager.execute_command(
            session, 
            phase_instruction,
            context
        )
    
    def _generate_phase_instruction(self, phase: Dict[str, Any]) -> str:
        """Generate instruction for a phase."""
        
        phase_type = phase.get("type", "general")
        description = phase.get("description", "")
        
        if phase_type == "setup":
            return f"Set up project structure and initial configuration: {description}"
        elif phase_type == "implementation":
            return f"Implement core functionality: {description}"
        elif phase_type == "testing":
            return f"Implement and run tests: {description}"
        elif phase_type == "deployment":
            return f"Deploy and configure application: {description}"
        elif phase_type == "validation":
            return f"Validate implementation: {description}"
        else:
            return f"Execute phase: {description}"
    
    async def _verify_phase_completion(
        self, 
        session: CursorSession, 
        phase: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify phase completion."""
        
        verification_checks = phase.get("verification_checks", [])
        
        for check in verification_checks:
            check_result = await self.cli_manager.execute_command(
                session, 
                check.get("command", ""),
                check.get("context", {})
            )
            
            if not check_result.success:
                return {
                    "success": False,
                    "failed_check": check,
                    "error": check_result.error
                }
        
        return {"success": True}
    
    async def _attempt_recovery(
        self, 
        session: CursorSession, 
        phase: Dict[str, Any],
        verification: Dict[str, Any]
    ) -> CursorExecutionResult:
        """Attempt recovery from phase failure."""
        
        recovery_commands = phase.get("recovery_commands", [])
        
        for recovery_cmd in recovery_commands:
            result = await self.cli_manager.execute_command(
                session, 
                recovery_cmd,
                phase.get("context", {})
            )
            
            if result.success:
                return result
        
        return CursorExecutionResult(
            success=False,
            output="",
            error="Recovery failed - all recovery commands failed"
        )

@dataclass
class OrchestrationExecutionResult:
    """Result of orchestration execution."""
    success: bool
    session_id: Optional[str]
    phases_executed: int
    results: List[CursorExecutionResult]
    total_execution_time: float
    skills_activated: List[str]
    error: Optional[str] = None

class CursorSessionManager:
    """Manages Cursor sessions and their lifecycle."""
    
    def __init__(self):
        self.sessions: Dict[str, CursorSession] = {}
    
    async def create_session(self, project_path: Path) -> CursorSession:
        """Create a new session."""
        # Implementation would create and manage sessions
        pass
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up expired sessions."""
        current_time = asyncio.get_event_loop().time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            age_hours = (current_time - session.created_at) / 3600
            if age_hours > max_age_hours:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.cleanup_session(session_id)
        
        return len(expired_sessions)
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up a specific session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False