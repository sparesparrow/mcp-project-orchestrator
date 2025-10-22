"""
OpenSSL Ecosystem Workflow Monitor

Monitors workflow runs across all OpenSSL repositories and provides
AI-assisted failure analysis and automated issue creation.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import httpx
from github import Github
from github.WorkflowRun import WorkflowRun
from github.Repository import Repository

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of workflow failures for classification."""
    BUILD_ERROR = "build_error"
    TEST_FAILURE = "test_failure"
    SECURITY_SCAN = "security_scan"
    DEPENDENCY_ISSUE = "dependency_issue"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    CACHE_ISSUE = "cache_issue"
    UNKNOWN = "unknown"


@dataclass
class WorkflowFailure:
    """Represents a workflow failure with context."""
    repository: str
    workflow_name: str
    run_id: int
    failure_type: FailureType
    error_message: str
    failed_at: datetime
    duration: int
    platform: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    actor: Optional[str] = None


@dataclass
class FailurePattern:
    """Represents a recurring failure pattern."""
    failure_type: FailureType
    repositories: List[str]
    frequency: int
    first_seen: datetime
    last_seen: datetime
    common_error: str
    suggested_fix: str


class EcosystemMonitor:
    """Monitors OpenSSL ecosystem workflows and analyzes failures."""
    
    def __init__(self, github_token: str, repositories: List[str]):
        self.github = Github(github_token)
        self.repositories = repositories
        self.failure_patterns: Dict[str, FailurePattern] = {}
        
    async def monitor_workflows(self, hours_back: int = 4) -> List[WorkflowFailure]:
        """Monitor workflows across all repositories for failures."""
        failures = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        for repo_name in self.repositories:
            try:
                repo = self.github.get_repo(repo_name)
                workflow_runs = repo.get_workflow_runs(
                    status="completed",
                    created=f">={cutoff_time.isoformat()}"
                )
                
                for run in workflow_runs:
                    if run.conclusion == "failure":
                        failure = await self._analyze_failure(run, repo_name)
                        if failure:
                            failures.append(failure)
                            
            except Exception as e:
                logger.error(f"Error monitoring {repo_name}: {e}")
                
        return failures
    
    async def _analyze_failure(self, run: WorkflowRun, repo_name: str) -> Optional[WorkflowFailure]:
        """Analyze a failed workflow run and classify the failure."""
        try:
            # Get workflow run details
            run_details = run.get_workflow_run()
            jobs = run_details.get_jobs()
            
            # Find the failed job
            failed_job = None
            for job in jobs:
                if job.conclusion == "failure":
                    failed_job = job
                    break
            
            if not failed_job:
                return None
                
            # Get job logs
            logs = failed_job.get_logs()
            error_message = self._extract_error_message(logs)
            
            # Classify failure type
            failure_type = self._classify_failure(error_message, failed_job.name)
            
            return WorkflowFailure(
                repository=repo_name,
                workflow_name=run.name,
                run_id=run.id,
                failure_type=failure_type,
                error_message=error_message,
                failed_at=run.created_at,
                duration=run.run_duration_ms or 0,
                platform=self._extract_platform(failed_job.name),
                branch=run.head_branch,
                commit_sha=run.head_sha,
                actor=run.actor.login if run.actor else None
            )
            
        except Exception as e:
            logger.error(f"Error analyzing failure in {repo_name} run {run.id}: {e}")
            return None
    
    def _extract_error_message(self, logs: str) -> str:
        """Extract the most relevant error message from job logs."""
        lines = logs.split('\n')
        
        # Look for common error patterns
        error_indicators = [
            "ERROR:", "FAILED:", "Exception:", "Error:", 
            "fatal:", "error:", "failed:", "FAIL:"
        ]
        
        for line in reversed(lines):
            if any(indicator in line for indicator in error_indicators):
                return line.strip()
                
        # Fallback to last few lines
        return '\n'.join(lines[-5:]).strip()
    
    def _classify_failure(self, error_message: str, job_name: str) -> FailureType:
        """Classify the type of failure based on error message and job name."""
        error_lower = error_message.lower()
        job_lower = job_name.lower()
        
        if "timeout" in error_lower or "timed out" in error_lower:
            return FailureType.TIMEOUT
        elif "permission denied" in error_lower or "unauthorized" in error_lower:
            return FailureType.PERMISSION_DENIED
        elif "cache" in error_lower and ("miss" in error_lower or "invalid" in error_lower):
            return FailureType.CACHE_ISSUE
        elif "dependency" in error_lower or "package not found" in error_lower:
            return FailureType.DEPENDENCY_ISSUE
        elif "security" in job_lower or "scan" in job_lower:
            return FailureType.SECURITY_SCAN
        elif "test" in job_lower or "pytest" in error_lower:
            return FailureType.TEST_FAILURE
        elif "build" in job_lower or "cmake" in error_lower or "conan" in error_lower:
            return FailureType.BUILD_ERROR
        else:
            return FailureType.UNKNOWN
    
    def _extract_platform(self, job_name: str) -> Optional[str]:
        """Extract platform information from job name."""
        platforms = ["linux", "windows", "macos", "ubuntu", "centos", "alpine"]
        for platform in platforms:
            if platform in job_name.lower():
                return platform
        return None
    
    def analyze_patterns(self, failures: List[WorkflowFailure]) -> List[FailurePattern]:
        """Analyze failures to identify recurring patterns."""
        patterns = {}
        
        # Group failures by type and error message
        for failure in failures:
            key = f"{failure.failure_type.value}:{failure.error_message[:100]}"
            
            if key not in patterns:
                patterns[key] = {
                    'failures': [],
                    'repositories': set(),
                    'first_seen': failure.failed_at,
                    'last_seen': failure.failed_at
                }
            
            patterns[key]['failures'].append(failure)
            patterns[key]['repositories'].add(failure.repository)
            patterns[key]['last_seen'] = max(patterns[key]['last_seen'], failure.failed_at)
            patterns[key]['first_seen'] = min(patterns[key]['first_seen'], failure.failed_at)
        
        # Convert to FailurePattern objects
        failure_patterns = []
        for key, data in patterns.items():
            if len(data['failures']) >= 2:  # Only patterns with 2+ occurrences
                failure_type = data['failures'][0].failure_type
                common_error = data['failures'][0].error_message
                
                pattern = FailurePattern(
                    failure_type=failure_type,
                    repositories=list(data['repositories']),
                    frequency=len(data['failures']),
                    first_seen=data['first_seen'],
                    last_seen=data['last_seen'],
                    common_error=common_error,
                    suggested_fix=self._generate_fix_suggestion(failure_type, common_error)
                )
                failure_patterns.append(pattern)
        
        return failure_patterns
    
    def _generate_fix_suggestion(self, failure_type: FailureType, error_message: str) -> str:
        """Generate AI-assisted fix suggestions based on failure type."""
        suggestions = {
            FailureType.BUILD_ERROR: """
**Build Error Fix Suggestions:**
1. Check Conan profile compatibility
2. Verify dependency versions in conanfile.py
3. Clear Conan cache: `conan cache clean`
4. Update build tools and compilers
5. Check for missing system dependencies
            """,
            FailureType.TEST_FAILURE: """
**Test Failure Fix Suggestions:**
1. Review test logs for specific assertion failures
2. Check test data and fixtures
3. Verify test environment setup
4. Update test expectations if behavior changed
5. Check for flaky tests and add retries
            """,
            FailureType.SECURITY_SCAN: """
**Security Scan Fix Suggestions:**
1. Update vulnerable dependencies
2. Review security scan reports in GitHub Security tab
3. Address CRITICAL and HIGH severity issues first
4. Update SBOM generation if needed
5. Check for hardcoded secrets or credentials
            """,
            FailureType.DEPENDENCY_ISSUE: """
**Dependency Issue Fix Suggestions:**
1. Verify Conan remote configuration
2. Check package availability in remote
3. Update package versions in conanfile.py
4. Clear and rebuild Conan cache
5. Check network connectivity to package registry
            """,
            FailureType.TIMEOUT: """
**Timeout Fix Suggestions:**
1. Increase workflow timeout limits
2. Optimize build process (parallel builds, caching)
3. Check for resource constraints
4. Review long-running operations
5. Consider splitting large jobs into smaller ones
            """,
            FailureType.PERMISSION_DENIED: """
**Permission Denied Fix Suggestions:**
1. Check OIDC configuration and permissions
2. Verify repository secrets and environment variables
3. Review GitHub Actions permissions
4. Check Cloudsmith API key or OIDC setup
5. Verify workflow file permissions
            """,
            FailureType.CACHE_ISSUE: """
**Cache Issue Fix Suggestions:**
1. Clear GitHub Actions cache
2. Update cache keys to include relevant changes
3. Check cache size limits
4. Verify cache restoration logic
5. Consider cache invalidation strategy
            """
        }
        
        base_suggestion = suggestions.get(failure_type, "Review error logs and check common failure causes.")
        
        # Add specific error context if available
        if "conan" in error_message.lower():
            base_suggestion += "\n\n**Conan-specific:** Check Conan configuration, remotes, and package availability."
        elif "cmake" in error_message.lower():
            base_suggestion += "\n\n**CMake-specific:** Verify CMakeLists.txt configuration and build settings."
        elif "docker" in error_message.lower():
            base_suggestion += "\n\n**Docker-specific:** Check Dockerfile syntax and base image availability."
            
        return base_suggestion.strip()


class IssueCreator:
    """Creates GitHub issues for recurring failure patterns."""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token)
    
    async def create_failure_issue(self, pattern: FailurePattern, target_repo: str) -> Optional[int]:
        """Create a GitHub issue for a failure pattern."""
        try:
            repo = self.github.get_repo(target_repo)
            
            title = f"🚨 Recurring {pattern.failure_type.value.replace('_', ' ').title()} Pattern Detected"
            
            body = f"""
## Failure Pattern Analysis

**Pattern Type:** {pattern.failure_type.value.replace('_', ' ').title()}
**Frequency:** {pattern.frequency} occurrences
**Repositories Affected:** {', '.join(pattern.repositories)}
**First Seen:** {pattern.first_seen.isoformat()}
**Last Seen:** {pattern.last_seen.isoformat()}

### Common Error
```
{pattern.common_error}
```

### Suggested Fix
{pattern.suggested_fix}

### Next Steps
1. Review the error pattern and suggested fixes
2. Implement the recommended solution
3. Monitor for recurrence
4. Close this issue once resolved

---
*This issue was automatically created by the OpenSSL Ecosystem Monitor*
            """
            
            labels = ["bug", "automated", "ecosystem-monitor"]
            if pattern.failure_type == FailureType.SECURITY_SCAN:
                labels.append("security")
            elif pattern.failure_type == FailureType.BUILD_ERROR:
                labels.append("build")
            elif pattern.failure_type == FailureType.TEST_FAILURE:
                labels.append("tests")
            
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels
            )
            
            logger.info(f"Created issue #{issue.number} in {target_repo} for {pattern.failure_type.value}")
            return issue.number
            
        except Exception as e:
            logger.error(f"Error creating issue in {target_repo}: {e}")
            return None


async def main():
    """Main monitoring function."""
    # Configuration
    GITHUB_TOKEN = "your-github-token"  # Should come from environment
    REPOSITORIES = [
        "sparesparrow/openssl",
        "sparesparrow/openssl-conan-base", 
        "sparesparrow/openssl-fips-policy",
        "sparesparrow/openssl-tools",
        "sparesparrow/mcp-project-orchestrator"
    ]
    
    # Initialize monitor
    monitor = EcosystemMonitor(GITHUB_TOKEN, REPOSITORIES)
    issue_creator = IssueCreator(GITHUB_TOKEN)
    
    # Monitor workflows
    logger.info("Starting ecosystem monitoring...")
    failures = await monitor.monitor_workflows(hours_back=4)
    
    if not failures:
        logger.info("No failures detected in the last 4 hours")
        return
    
    logger.info(f"Found {len(failures)} failures across {len(set(f.repository for f in failures))} repositories")
    
    # Analyze patterns
    patterns = monitor.analyze_patterns(failures)
    logger.info(f"Identified {len(patterns)} recurring failure patterns")
    
    # Create issues for significant patterns
    for pattern in patterns:
        if pattern.frequency >= 3:  # Only create issues for patterns with 3+ occurrences
            # Create issue in the most affected repository
            main_repo = max(pattern.repositories, key=lambda r: sum(1 for f in failures if f.repository == r))
            issue_number = await issue_creator.create_failure_issue(pattern, main_repo)
            
            if issue_number:
                logger.info(f"Created issue #{issue_number} for pattern: {pattern.failure_type.value}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())