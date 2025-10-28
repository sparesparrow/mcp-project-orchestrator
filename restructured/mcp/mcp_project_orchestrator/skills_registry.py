#!/usr/bin/env python3
"""
Skills Registry and Discovery Engine for MCP Project Orchestrator.

This module implements a comprehensive Skills registry that enables automatic
skill discovery, composition, and orchestration for AI-assisted project development.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class SkillType(Enum):
    """Types of skills available in the registry."""
    ORCHESTRATION = "orchestration"
    VALIDATION = "validation"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CRYPTO = "crypto"
    FIPS = "fips"

class SkillPriority(Enum):
    """Priority levels for skill activation."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class SkillMetadata:
    """Metadata for a skill in the registry."""
    skill_id: str
    name: str
    description: str
    skill_type: SkillType
    priority: SkillPriority
    triggers: List[str]
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    token_budget: int = 1000
    execution_timeout: int = 30
    version: str = "1.0.0"
    author: str = "mcp-project-orchestrator"
    tags: List[str] = field(default_factory=list)
    progressive_files: Dict[str, str] = field(default_factory=dict)
    verification_required: bool = False
    auto_compose: bool = True

@dataclass
class ProjectContext:
    """Context information for project orchestration."""
    project_idea: str
    project_type: str
    technologies: List[str]
    requirements: List[str]
    constraints: Dict[str, Any]
    objectives: List[str]
    security_level: str = "standard"
    fips_required: bool = False
    platform_targets: List[str] = field(default_factory=lambda: ["multi-platform"])

@dataclass
class SkillComposition:
    """Composition of multiple skills for execution."""
    skills: List[SkillMetadata]
    execution_order: List[str]
    dependency_graph: Dict[str, List[str]]
    total_token_budget: int
    estimated_execution_time: int
    verification_plan: List[str]

class SkillDiscoveryEngine:
    """Engine for discovering relevant skills based on project context."""
    
    def __init__(self):
        self.trigger_index = defaultdict(list)
        self.skill_index = {}
        self.context_analyzer = ContextAnalyzer()
    
    async def find_skills_by_trigger(self, trigger: str) -> List[SkillMetadata]:
        """Find skills that match a specific trigger."""
        trigger_lower = trigger.lower()
        matching_skills = []
        
        for skill_id, skill in self.skill_index.items():
            for skill_trigger in skill.triggers:
                if trigger_lower in skill_trigger.lower() or skill_trigger.lower() in trigger_lower:
                    matching_skills.append(skill)
                    break
        
        return matching_skills
    
    async def find_skills_by_context(self, context: ProjectContext) -> List[SkillMetadata]:
        """Find skills based on comprehensive project context."""
        all_triggers = self.context_analyzer.extract_triggers(context)
        candidate_skills = set()
        
        # Find skills by individual triggers
        for trigger in all_triggers:
            matching_skills = await self.find_skills_by_trigger(trigger)
            candidate_skills.update(matching_skills)
        
        # Find skills by project type
        type_skills = await self.find_skills_by_project_type(context.project_type)
        candidate_skills.update(type_skills)
        
        # Find skills by technology stack
        tech_skills = await self.find_skills_by_technologies(context.technologies)
        candidate_skills.update(tech_skills)
        
        # Find skills by security requirements
        if context.fips_required or context.security_level == "high":
            security_skills = await self.find_security_skills()
            candidate_skills.update(security_skills)
        
        return list(candidate_skills)
    
    async def find_skills_by_project_type(self, project_type: str) -> List[SkillMetadata]:
        """Find skills specific to project type."""
        type_mapping = {
            "microservices": ["microservice-orchestration", "service-discovery", "circuit-breaker"],
            "event-driven": ["event-orchestration", "message-queue", "event-sourcing"],
            "serverless": ["serverless-orchestration", "function-deployment", "cloud-integration"],
            "openssl": ["fips-compliance", "crypto-patterns", "security-validation"],
            "web-application": ["web-orchestration", "api-design", "frontend-integration"]
        }
        
        relevant_skills = []
        for skill_id in type_mapping.get(project_type.lower(), []):
            if skill_id in self.skill_index:
                relevant_skills.append(self.skill_index[skill_id])
        
        return relevant_skills
    
    async def find_skills_by_technologies(self, technologies: List[str]) -> List[SkillMetadata]:
        """Find skills based on technology stack."""
        tech_skills = []
        for tech in technologies:
            tech_lower = tech.lower()
            for skill_id, skill in self.skill_index.items():
                if any(tech_lower in tag.lower() for tag in skill.tags):
                    tech_skills.append(skill)
        
        return tech_skills
    
    async def find_security_skills(self) -> List[SkillMetadata]:
        """Find security-related skills."""
        security_skills = []
        for skill_id, skill in self.skill_index.items():
            if skill.skill_type in [SkillType.SECURITY, SkillType.FIPS, SkillType.CRYPTO]:
                security_skills.append(skill)
        
        return security_skills

class ContextAnalyzer:
    """Analyzes project context to extract relevant triggers and requirements."""
    
    def extract_triggers(self, context: ProjectContext) -> List[str]:
        """Extract skill triggers from project context."""
        triggers = []
        
        # Extract from project idea
        idea_words = re.findall(r'\b\w+\b', context.project_idea.lower())
        triggers.extend(idea_words)
        
        # Extract from technologies
        triggers.extend([tech.lower() for tech in context.technologies])
        
        # Extract from requirements
        for req in context.requirements:
            req_words = re.findall(r'\b\w+\b', req.lower())
            triggers.extend(req_words)
        
        # Add project type specific triggers
        if context.project_type:
            triggers.append(context.project_type.lower())
        
        # Add security triggers
        if context.fips_required:
            triggers.extend(["fips", "crypto", "security", "openssl"])
        
        if context.security_level == "high":
            triggers.extend(["security", "validation", "compliance"])
        
        return list(set(triggers))  # Remove duplicates

class SkillCompositionEngine:
    """Engine for composing skills into executable workflows."""
    
    def __init__(self):
        self.dependency_resolver = DependencyResolver()
        self.optimizer = SkillOptimizer()
    
    async def compose_skills(
        self, 
        skills: List[SkillMetadata], 
        context: ProjectContext
    ) -> SkillComposition:
        """Compose skills into an executable workflow."""
        
        # Resolve dependencies
        dependency_graph = await self.dependency_resolver.resolve_dependencies(skills)
        
        # Create execution order
        execution_order = await self.dependency_resolver.topological_sort(dependency_graph)
        
        # Optimize composition
        optimized_skills = await self.optimizer.optimize_skill_selection(
            skills, context, dependency_graph
        )
        
        # Calculate resource requirements
        total_token_budget = sum(skill.token_budget for skill in optimized_skills)
        estimated_execution_time = sum(skill.execution_timeout for skill in optimized_skills)
        
        # Create verification plan
        verification_plan = await self.create_verification_plan(optimized_skills, context)
        
        return SkillComposition(
            skills=optimized_skills,
            execution_order=execution_order,
            dependency_graph=dependency_graph,
            total_token_budget=total_token_budget,
            estimated_execution_time=estimated_execution_time,
            verification_plan=verification_plan
        )
    
    async def create_verification_plan(
        self, 
        skills: List[SkillMetadata], 
        context: ProjectContext
    ) -> List[str]:
        """Create verification plan for skill composition."""
        verification_steps = []
        
        for skill in skills:
            if skill.verification_required:
                verification_steps.append(f"Verify {skill.name} execution")
            
            if skill.skill_type == SkillType.SECURITY:
                verification_steps.append(f"Security validation for {skill.name}")
            
            if skill.skill_type == SkillType.FIPS:
                verification_steps.append(f"FIPS compliance check for {skill.name}")
        
        return verification_steps

class DependencyResolver:
    """Resolves dependencies between skills."""
    
    async def resolve_dependencies(self, skills: List[SkillMetadata]) -> Dict[str, List[str]]:
        """Resolve skill dependencies into a dependency graph."""
        dependency_graph = defaultdict(list)
        
        for skill in skills:
            for dep_id in skill.dependencies:
                if dep_id in [s.skill_id for s in skills]:
                    dependency_graph[skill.skill_id].append(dep_id)
        
        return dict(dependency_graph)
    
    async def topological_sort(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort to determine execution order."""
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        # Build graph and calculate in-degrees
        for skill_id, deps in dependency_graph.items():
            for dep in deps:
                graph[dep].append(skill_id)
                in_degree[skill_id] += 1
        
        # Find all nodes with no incoming edges
        queue = [skill_id for skill_id in dependency_graph.keys() if in_degree[skill_id] == 0]
        
        result = []
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Remove current node and update in-degrees
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result

class SkillOptimizer:
    """Optimizes skill selection and composition."""
    
    async def optimize_skill_selection(
        self, 
        skills: List[SkillMetadata], 
        context: ProjectContext,
        dependency_graph: Dict[str, List[str]]
    ) -> List[SkillMetadata]:
        """Optimize skill selection based on context and constraints."""
        
        # Filter out conflicting skills
        filtered_skills = await self.remove_conflicting_skills(skills)
        
        # Rank skills by relevance
        ranked_skills = await self.rank_skills_by_relevance(filtered_skills, context)
        
        # Apply resource constraints
        optimized_skills = await self.apply_resource_constraints(ranked_skills, context)
        
        return optimized_skills
    
    async def remove_conflicting_skills(self, skills: List[SkillMetadata]) -> List[SkillMetadata]:
        """Remove skills that conflict with each other."""
        skill_map = {skill.skill_id: skill for skill in skills}
        valid_skills = []
        
        for skill in skills:
            has_conflict = False
            for conflict_id in skill.conflicts:
                if conflict_id in skill_map:
                    has_conflict = True
                    break
            
            if not has_conflict:
                valid_skills.append(skill)
        
        return valid_skills
    
    async def rank_skills_by_relevance(
        self, 
        skills: List[SkillMetadata], 
        context: ProjectContext
    ) -> List[SkillMetadata]:
        """Rank skills by relevance to project context."""
        
        def calculate_relevance_score(skill: SkillMetadata) -> float:
            score = 0.0
            
            # Priority score (lower is better)
            score += (5 - skill.priority.value) * 10
            
            # Trigger match score
            context_triggers = set(context.project_idea.lower().split())
            skill_triggers = set(trigger.lower() for trigger in skill.triggers)
            trigger_matches = len(context_triggers.intersection(skill_triggers))
            score += trigger_matches * 5
            
            # Technology match score
            tech_matches = sum(1 for tech in context.technologies 
                             if any(tech.lower() in tag.lower() for tag in skill.tags))
            score += tech_matches * 3
            
            # Security requirement match
            if context.fips_required and skill.skill_type == SkillType.FIPS:
                score += 20
            elif context.security_level == "high" and skill.skill_type == SkillType.SECURITY:
                score += 15
            
            return score
        
        return sorted(skills, key=calculate_relevance_score, reverse=True)
    
    async def apply_resource_constraints(
        self, 
        skills: List[SkillMetadata], 
        context: ProjectContext
    ) -> List[SkillMetadata]:
        """Apply resource constraints to skill selection."""
        
        # Default constraints
        max_tokens = context.constraints.get("max_tokens", 10000)
        max_execution_time = context.constraints.get("max_execution_time", 300)
        max_skills = context.constraints.get("max_skills", 10)
        
        selected_skills = []
        total_tokens = 0
        total_time = 0
        
        for skill in skills:
            if (len(selected_skills) < max_skills and 
                total_tokens + skill.token_budget <= max_tokens and
                total_time + skill.execution_timeout <= max_execution_time):
                
                selected_skills.append(skill)
                total_tokens += skill.token_budget
                total_time += skill.execution_timeout
        
        return selected_skills

class SkillsRegistry:
    """Main registry for managing and discovering skills."""
    
    def __init__(self, skills_catalog_path: Optional[str] = None):
        self.skills_catalog_path = skills_catalog_path or "skills_catalog.json"
        self.skill_index: Dict[str, SkillMetadata] = {}
        self.discovery_engine = SkillDiscoveryEngine()
        self.composition_engine = SkillCompositionEngine()
        self.verification_engine = SkillVerificationEngine()
        
        # Load skills catalog
        self._load_skills_catalog()
    
    def _load_skills_catalog(self) -> None:
        """Load skills from catalog file."""
        try:
            if Path(self.skills_catalog_path).exists():
                with open(self.skills_catalog_path, 'r') as f:
                    catalog_data = json.load(f)
                    self._load_skills_from_catalog(catalog_data)
            else:
                # Load default skills
                self._load_default_skills()
        except Exception as e:
            logger.error(f"Error loading skills catalog: {e}")
            self._load_default_skills()
    
    def _load_skills_from_catalog(self, catalog_data: Dict[str, Any]) -> None:
        """Load skills from catalog data."""
        for skill_data in catalog_data.get("skills", []):
            skill = SkillMetadata(
                skill_id=skill_data["skill_id"],
                name=skill_data["name"],
                description=skill_data["description"],
                skill_type=SkillType(skill_data["skill_type"]),
                priority=SkillPriority(skill_data["priority"]),
                triggers=skill_data["triggers"],
                dependencies=skill_data.get("dependencies", []),
                conflicts=skill_data.get("conflicts", []),
                token_budget=skill_data.get("token_budget", 1000),
                execution_timeout=skill_data.get("execution_timeout", 30),
                version=skill_data.get("version", "1.0.0"),
                author=skill_data.get("author", "mcp-project-orchestrator"),
                tags=skill_data.get("tags", []),
                progressive_files=skill_data.get("progressive_files", {}),
                verification_required=skill_data.get("verification_required", False),
                auto_compose=skill_data.get("auto_compose", True)
            )
            self.skill_index[skill.skill_id] = skill
            self.discovery_engine.skill_index[skill.skill_id] = skill
    
    def _load_default_skills(self) -> None:
        """Load default skills for common project types."""
        default_skills = [
            {
                "skill_id": "project-orchestration",
                "name": "Project Orchestration",
                "description": "Orchestrates project creation and setup",
                "skill_type": "orchestration",
                "priority": "high",
                "triggers": ["project", "create", "setup", "orchestrate"],
                "tags": ["general", "orchestration"]
            },
            {
                "skill_id": "fips-compliance",
                "name": "FIPS Compliance Validation",
                "description": "Validates FIPS 140-3 compliance for cryptographic code",
                "skill_type": "fips",
                "priority": "critical",
                "triggers": ["fips", "crypto", "openssl", "security", "compliance"],
                "tags": ["security", "fips", "crypto", "openssl"],
                "verification_required": True
            },
            {
                "skill_id": "security-validation",
                "name": "Security Validation",
                "description": "Validates security patterns and practices",
                "skill_type": "security",
                "priority": "high",
                "triggers": ["security", "validation", "secure", "safe"],
                "tags": ["security", "validation"]
            },
            {
                "skill_id": "microservice-orchestration",
                "name": "Microservice Orchestration",
                "description": "Orchestrates microservice architecture projects",
                "skill_type": "orchestration",
                "priority": "high",
                "triggers": ["microservice", "microservices", "distributed", "service"],
                "tags": ["microservices", "architecture", "distributed"]
            },
            {
                "skill_id": "cursor-integration",
                "name": "Cursor Integration",
                "description": "Integrates with Cursor IDE for development workflow",
                "skill_type": "deployment",
                "priority": "medium",
                "triggers": ["cursor", "ide", "development", "editor"],
                "tags": ["cursor", "ide", "development"]
            }
        ]
        
        for skill_data in default_skills:
            skill = SkillMetadata(
                skill_id=skill_data["skill_id"],
                name=skill_data["name"],
                description=skill_data["description"],
                skill_type=SkillType(skill_data["skill_type"]),
                priority=SkillPriority(skill_data["priority"]),
                triggers=skill_data["triggers"],
                tags=skill_data["tags"],
                verification_required=skill_data.get("verification_required", False)
            )
            self.skill_index[skill.skill_id] = skill
            self.discovery_engine.skill_index[skill.skill_id] = skill
    
    async def discover_skills(self, context: ProjectContext) -> List[SkillMetadata]:
        """Discover relevant skills for project context."""
        return await self.discovery_engine.find_skills_by_context(context)
    
    async def compose_skills(
        self, 
        skills: List[SkillMetadata], 
        context: ProjectContext
    ) -> SkillComposition:
        """Compose skills into executable workflow."""
        return await self.composition_engine.compose_skills(skills, context)
    
    async def discover_and_compose_skills(
        self, 
        context: ProjectContext
    ) -> SkillComposition:
        """Discover and compose skills for project orchestration."""
        
        # Discover relevant skills
        candidate_skills = await self.discover_skills(context)
        
        # Compose skills into workflow
        composition = await self.compose_skills(candidate_skills, context)
        
        # Verify composition
        verification = await self.verification_engine.verify_composition(
            composition, context
        )
        
        if not verification.valid:
            logger.warning(f"Skill composition verification failed: {verification.issues}")
            # Fallback to basic composition
            return await self._create_fallback_composition(context)
        
        return composition
    
    async def _create_fallback_composition(self, context: ProjectContext) -> SkillComposition:
        """Create fallback composition when verification fails."""
        fallback_skills = [
            self.skill_index["project-orchestration"]
        ]
        
        if context.fips_required:
            fallback_skills.append(self.skill_index["fips-compliance"])
        
        if context.security_level == "high":
            fallback_skills.append(self.skill_index["security-validation"])
        
        return SkillComposition(
            skills=fallback_skills,
            execution_order=[skill.skill_id for skill in fallback_skills],
            dependency_graph={},
            total_token_budget=sum(skill.token_budget for skill in fallback_skills),
            estimated_execution_time=sum(skill.execution_timeout for skill in fallback_skills),
            verification_plan=["Basic project orchestration"]
        )

class SkillVerificationEngine:
    """Engine for verifying skill compositions."""
    
    async def verify_composition(
        self, 
        composition: SkillComposition, 
        context: ProjectContext
    ) -> 'VerificationResult':
        """Verify skill composition for validity and completeness."""
        issues = []
        
        # Check for circular dependencies
        if self._has_circular_dependencies(composition.dependency_graph):
            issues.append("Circular dependencies detected in skill composition")
        
        # Check resource constraints
        if composition.total_token_budget > context.constraints.get("max_tokens", 10000):
            issues.append("Token budget exceeds constraints")
        
        if composition.estimated_execution_time > context.constraints.get("max_execution_time", 300):
            issues.append("Execution time exceeds constraints")
        
        # Check for missing critical skills
        if context.fips_required and not any(s.skill_type == SkillType.FIPS for s in composition.skills):
            issues.append("FIPS compliance skill missing for FIPS-required project")
        
        if context.security_level == "high" and not any(s.skill_type == SkillType.SECURITY for s in composition.skills):
            issues.append("Security validation skill missing for high-security project")
        
        return VerificationResult(valid=len(issues) == 0, issues=issues)

@dataclass
class VerificationResult:
    """Result of skill composition verification."""
    valid: bool
    issues: List[str]

def _has_circular_dependencies(self, dependency_graph: Dict[str, List[str]]) -> bool:
    """Check for circular dependencies in skill composition."""
    visited = set()
    rec_stack = set()
    
    def has_cycle(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in dependency_graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    for node in dependency_graph:
        if node not in visited:
            if has_cycle(node):
                return True
    
    return False

# Add the method to the class
SkillVerificationEngine._has_circular_dependencies = _has_circular_dependencies