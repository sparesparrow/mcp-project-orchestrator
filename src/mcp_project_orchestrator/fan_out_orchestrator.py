"""
Cross-Repository Release Fan-Out Orchestrator

Manages coordinated releases across the OpenSSL ecosystem by triggering
workflows in dependent repositories based on dependency relationships.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

import httpx
from github import Github
from github.Repository import Repository

logger = logging.getLogger(__name__)


class ReleaseType(Enum):
    """Types of releases that can trigger fan-out."""
    FOUNDATION = "foundation"  # openssl-conan-base, openssl-fips-policy
    TOOLING = "tooling"       # openssl-tools
    DOMAIN = "domain"         # openssl
    ORCHESTRATION = "orchestration"  # mcp-project-orchestrator


@dataclass
class RepositoryInfo:
    """Information about a repository in the ecosystem."""
    name: str
    full_name: str
    release_type: ReleaseType
    dependencies: List[str]
    dependents: List[str]
    version_file: Optional[str] = None
    conanfile_path: str = "conanfile.py"


@dataclass
class ReleaseTrigger:
    """Represents a release trigger for fan-out."""
    source_repo: str
    version: str
    release_type: ReleaseType
    triggered_at: datetime
    dependencies_updated: List[str]


class FanOutOrchestrator:
    """Orchestrates cross-repository releases and dependency updates."""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token)
        self.repositories = self._initialize_repositories()
        self.dependency_graph = self._build_dependency_graph()
        
    def _initialize_repositories(self) -> Dict[str, RepositoryInfo]:
        """Initialize repository information."""
        return {
            "openssl-conan-base": RepositoryInfo(
                name="openssl-conan-base",
                full_name="sparesparrow/openssl-conan-base",
                release_type=ReleaseType.FOUNDATION,
                dependencies=[],
                dependents=["openssl-tools"],
                version_file=None,
                conanfile_path="conanfile.py"
            ),
            "openssl-fips-policy": RepositoryInfo(
                name="openssl-fips-policy",
                full_name="sparesparrow/openssl-fips-policy",
                release_type=ReleaseType.FOUNDATION,
                dependencies=[],
                dependents=["openssl-tools"],
                version_file=None,
                conanfile_path="conanfile.py"
            ),
            "openssl-tools": RepositoryInfo(
                name="openssl-tools",
                full_name="sparesparrow/openssl-tools",
                release_type=ReleaseType.TOOLING,
                dependencies=["openssl-conan-base", "openssl-fips-policy"],
                dependents=["openssl"],
                version_file=None,
                conanfile_path="conanfile.py"
            ),
            "openssl": RepositoryInfo(
                name="openssl",
                full_name="sparesparrow/openssl",
                release_type=ReleaseType.DOMAIN,
                dependencies=["openssl-tools"],
                dependents=[],
                version_file="VERSION.dat",
                conanfile_path="conanfile.py"
            ),
            "mcp-project-orchestrator": RepositoryInfo(
                name="mcp-project-orchestrator",
                full_name="sparesparrow/mcp-project-orchestrator",
                release_type=ReleaseType.ORCHESTRATION,
                dependencies=[],
                dependents=[],
                version_file=None,
                conanfile_path="conanfile.py"
            )
        }
    
    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph for release ordering."""
        graph = {}
        for repo_name, repo_info in self.repositories.items():
            graph[repo_name] = set(repo_info.dependencies)
        return graph
    
    async def trigger_release_cascade(self, source_repo: str, version: str, 
                                    release_type: ReleaseType) -> List[ReleaseTrigger]:
        """Trigger a release cascade starting from a source repository."""
        triggers = []
        
        # Create initial trigger
        initial_trigger = ReleaseTrigger(
            source_repo=source_repo,
            version=version,
            release_type=release_type,
            triggered_at=datetime.utcnow(),
            dependencies_updated=[]
        )
        triggers.append(initial_trigger)
        
        # Find all dependent repositories
        dependents = self._get_all_dependents(source_repo)
        
        # Trigger releases in dependency order
        for dependent in dependents:
            try:
                success = await self._trigger_dependent_release(
                    dependent, source_repo, version
                )
                if success:
                    trigger = ReleaseTrigger(
                        source_repo=dependent,
                        version=version,
                        release_type=self.repositories[dependent].release_type,
                        triggered_at=datetime.utcnow(),
                        dependencies_updated=[source_repo]
                    )
                    triggers.append(trigger)
                    logger.info(f"Successfully triggered release in {dependent}")
                else:
                    logger.error(f"Failed to trigger release in {dependent}")
                    
            except Exception as e:
                logger.error(f"Error triggering release in {dependent}: {e}")
        
        return triggers
    
    def _get_all_dependents(self, repo_name: str) -> List[str]:
        """Get all repositories that depend on the given repository."""
        dependents = set()
        to_process = [repo_name]
        
        while to_process:
            current = to_process.pop(0)
            for repo_name_check, repo_info in self.repositories.items():
                if current in repo_info.dependencies and repo_name_check not in dependents:
                    dependents.add(repo_name_check)
                    to_process.append(repo_name_check)
        
        return list(dependents)
    
    async def _trigger_dependent_release(self, dependent_repo: str, 
                                       source_repo: str, version: str) -> bool:
        """Trigger a release in a dependent repository."""
        try:
            repo = self.github.get_repo(self.repositories[dependent_repo].full_name)
            
            # Trigger workflow_dispatch event
            workflow_dispatch_inputs = {
                "source_repository": source_repo,
                "source_version": version,
                "dependency_update": "true",
                "triggered_by": "fan-out-orchestrator"
            }
            
            # Find the appropriate workflow to trigger
            workflows = repo.get_workflows()
            target_workflow = None
            
            for workflow in workflows:
                if workflow.name.lower() in ["release", "build", "ci"]:
                    target_workflow = workflow
                    break
            
            if not target_workflow:
                logger.warning(f"No suitable workflow found in {dependent_repo}")
                return False
            
            # Dispatch the workflow
            target_workflow.create_dispatch(
                ref="main",  # or get default branch
                inputs=workflow_dispatch_inputs
            )
            
            logger.info(f"Dispatched workflow in {dependent_repo}")
            return True
            
        except Exception as e:
            logger.error(f"Error dispatching workflow in {dependent_repo}: {e}")
            return False
    
    async def update_dependency_versions(self, repo_name: str, 
                                       dependency_updates: Dict[str, str]) -> bool:
        """Update dependency versions in a repository's conanfile.py."""
        try:
            repo = self.github.get_repo(self.repositories[repo_name].full_name)
            
            # Get the conanfile.py content
            conanfile_content = repo.get_contents(
                self.repositories[repo_name].conanfile_path
            ).decoded_content.decode('utf-8')
            
            # Update dependency versions
            updated_content = conanfile_content
            for dep_name, new_version in dependency_updates.items():
                # Simple string replacement - in production, use proper parsing
                old_pattern = f'"{dep_name}/'
                new_pattern = f'"{dep_name}/{new_version}@'
                updated_content = updated_content.replace(old_pattern, new_pattern)
            
            # Create a new branch and commit
            branch_name = f"update-dependencies-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Get default branch
            default_branch = repo.default_branch
            
            # Create new branch
            ref = repo.get_git_ref(f"heads/{default_branch}")
            repo.create_git_ref(f"refs/heads/{branch_name}", ref.object.sha)
            
            # Update file
            repo.update_file(
                path=self.repositories[repo_name].conanfile_path,
                message=f"Update dependencies: {', '.join(f'{k}={v}' for k, v in dependency_updates.items())}",
                content=updated_content,
                sha=repo.get_contents(
                    self.repositories[repo_name].conanfile_path
                ).sha,
                branch=branch_name
            )
            
            # Create pull request
            pr = repo.create_pull(
                title=f"Update dependencies from {list(dependency_updates.keys())[0]}",
                body=f"""
## Dependency Updates

This PR updates the following dependencies:

{chr(10).join(f'- **{dep}**: {version}' for dep, version in dependency_updates.items())}

### Changes
- Updated `conanfile.py` with new dependency versions
- Triggered by fan-out orchestrator from {list(dependency_updates.keys())[0]}

### Testing
- [ ] Verify builds pass with new dependencies
- [ ] Run integration tests
- [ ] Check for any breaking changes

---
*This PR was automatically created by the Fan-Out Orchestrator*
                """,
                head=branch_name,
                base=default_branch
            )
            
            logger.info(f"Created PR #{pr.number} in {repo_name} for dependency updates")
            return True
            
        except Exception as e:
            logger.error(f"Error updating dependencies in {repo_name}: {e}")
            return False
    
    async def get_release_status(self, triggers: List[ReleaseTrigger]) -> Dict[str, str]:
        """Get the status of release triggers."""
        status = {}
        
        for trigger in triggers:
            try:
                repo = self.github.get_repo(self.repositories[trigger.source_repo].full_name)
                workflows = repo.get_workflow_runs(
                    head_sha=trigger.triggered_at.isoformat(),
                    per_page=10
                )
                
                # Find the most recent workflow run
                latest_run = None
                for run in workflows:
                    if run.created_at >= trigger.triggered_at:
                        latest_run = run
                        break
                
                if latest_run:
                    status[trigger.source_repo] = latest_run.conclusion or latest_run.status
                else:
                    status[trigger.source_repo] = "not_found"
                    
            except Exception as e:
                logger.error(f"Error getting status for {trigger.source_repo}: {e}")
                status[trigger.source_repo] = "error"
        
        return status


class ReleaseCoordinator:
    """Coordinates releases across the OpenSSL ecosystem."""
    
    def __init__(self, github_token: str):
        self.orchestrator = FanOutOrchestrator(github_token)
    
    async def coordinate_foundation_release(self, version: str) -> Dict[str, any]:
        """Coordinate a foundation layer release (openssl-conan-base or openssl-fips-policy)."""
        logger.info(f"Coordinating foundation release: {version}")
        
        # Trigger tooling layer updates
        tooling_triggers = await self.orchestrator.trigger_release_cascade(
            "openssl-tools", version, ReleaseType.TOOLING
        )
        
        return {
            "foundation_version": version,
            "tooling_triggers": tooling_triggers,
            "status": "coordinated"
        }
    
    async def coordinate_tooling_release(self, version: str) -> Dict[str, any]:
        """Coordinate a tooling layer release (openssl-tools)."""
        logger.info(f"Coordinating tooling release: {version}")
        
        # Trigger domain layer updates
        domain_triggers = await self.orchestrator.trigger_release_cascade(
            "openssl", version, ReleaseType.DOMAIN
        )
        
        return {
            "tooling_version": version,
            "domain_triggers": domain_triggers,
            "status": "coordinated"
        }
    
    async def coordinate_domain_release(self, version: str) -> Dict[str, any]:
        """Coordinate a domain layer release (openssl)."""
        logger.info(f"Coordinating domain release: {version}")
        
        # Domain releases don't trigger other releases
        # but we can update orchestration layer if needed
        orchestration_triggers = await self.orchestrator.trigger_release_cascade(
            "mcp-project-orchestrator", version, ReleaseType.ORCHESTRATION
        )
        
        return {
            "domain_version": version,
            "orchestration_triggers": orchestration_triggers,
            "status": "coordinated"
        }


async def main():
    """Main orchestration function."""
    # Configuration
    GITHUB_TOKEN = "your-github-token"  # Should come from environment
    
    # Initialize coordinator
    coordinator = ReleaseCoordinator(GITHUB_TOKEN)
    
    # Example: Coordinate a tooling release
    result = await coordinator.coordinate_tooling_release("1.2.5")
    logger.info(f"Release coordination result: {result}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())