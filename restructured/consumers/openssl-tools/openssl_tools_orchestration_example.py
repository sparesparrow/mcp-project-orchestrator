#!/usr/bin/env python3
"""
OpenSSL Tools Orchestration Example.

This example demonstrates how to use the OpenSSL Tools Orchestration system
to create a complete project setup with Skills-enabled automation.
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_project_orchestrator.openssl_orchestration_main import OpenSSLOrchestrationMain
from mcp_project_orchestrator.openssl_tools_orchestration import (
    OpenSSLProjectContext,
    OpenSSLProjectType,
    BuildPlatform,
    CursorExecutionMode
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def example_openssl_tools_orchestration():
    """Example of OpenSSL tools orchestration."""
    
    print("🚀 OpenSSL Tools Orchestration Example")
    print("=" * 50)
    
    # Initialize the orchestration system
    orchestration_main = OpenSSLOrchestrationMain()
    
    # Example 1: Create a complete OpenSSL tools project
    print("\n📁 Example 1: Creating OpenSSL Tools Project")
    print("-" * 40)
    
    project_context = OpenSSLProjectContext(
        project_type=OpenSSLProjectType.OPENSSL_TOOLS,
        repository_url="https://github.com/sparesparrow/openssl-tools",
        target_platforms=[
            BuildPlatform.LINUX_GCC11,
            BuildPlatform.WINDOWS_MSVC193,
            BuildPlatform.MACOS_ARM64
        ],
        fips_required=True,
        ci_cd_enabled=True,
        testing_framework="pytest",
        build_tools=["cmake", "make", "gcc", "clang"],
        dependencies=["openssl", "zlib", "libssl-dev"],
        security_level="high",
        compliance_requirements=["FIPS-140-3", "SOC2"]
    )
    
    # Execute orchestration
    result = await orchestration_main.openssl_orchestrator.orchestrate_openssl_tools_project(
        project_context,
        CursorExecutionMode.AUTONOMOUS
    )
    
    print(f"✅ Project Creation: {'Success' if result['success'] else 'Failed'}")
    print(f"📂 Project Path: {result['project_path']}")
    print(f"🔧 Skills Applied: {len(result['skills_applied'])}")
    print(f"⚙️ Workflows Generated: {result['workflows_generated']}")
    print(f"🏗️ Build Configs: {result['build_configs_generated']}")
    print(f"🧪 Testing Framework: {'Success' if result['testing_framework']['success'] else 'Failed'}")
    print(f"🔒 FIPS Framework: {'Success' if result['fips_framework']['success'] else 'Failed'}")
    print(f"⏱️ Execution Time: {result['execution_time']:.2f}s")
    
    # Example 2: Create GitHub Actions CI workflow
    print("\n🔄 Example 2: Creating GitHub Actions CI Workflow")
    print("-" * 50)
    
    ci_result = await orchestration_main.mcp_server.tools["create_openssl_ci_workflow"](
        project_type="openssl_tools",
        repository_url="https://github.com/sparesparrow/openssl-tools",
        target_platforms=["linux-gcc11", "windows-msvc193", "macos-arm64"],
        fips_required=True,
        ci_cd_enabled=True,
        testing_framework="pytest",
        execution_mode="autonomous"
    )
    
    print(f"✅ CI Workflow Creation: {'Success' if ci_result['success'] else 'Failed'}")
    if ci_result['success']:
        print(f"📋 Workflow Name: {ci_result['workflow_name']}")
        print(f"🖥️ Platforms: {', '.join(ci_result['platforms'])}")
        print(f"🔀 Triggers: {', '.join(ci_result['triggers'])}")
        
        # Save workflow YAML
        workflow_file = Path("openssl-tools-ci.yml")
        workflow_file.write_text(ci_result['workflow_yaml'])
        print(f"💾 Workflow saved to: {workflow_file}")
    
    # Example 3: FIPS Compliance Validation
    print("\n🔒 Example 3: FIPS Compliance Validation")
    print("-" * 40)
    
    # Sample OpenSSL code changes
    sample_code_changes = [
        """
def encrypt_data(data: bytes, key: bytes) -> bytes:
    # Using AES-256-GCM for encryption
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return ciphertext
        """,
        """
def generate_key() -> bytes:
    # Generate cryptographically secure random key
    return os.urandom(32)  # 256 bits for AES-256
        """,
        """
def compare_keys(key1: bytes, key2: bytes) -> bool:
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(key1, key2)
        """
    ]
    
    fips_context = {
        "file_path": "src/crypto/encryption.py",
        "module_type": "cryptographic",
        "fips_required": True,
        "security_level": "high"
    }
    
    fips_result = await orchestration_main.mcp_server.tools["validate_openssl_fips_compliance"](
        code_changes=sample_code_changes,
        fips_context=fips_context
    )
    
    print(f"✅ FIPS Validation: {'Success' if fips_result['success'] else 'Failed'}")
    print(f"🔍 Compliant: {'Yes' if fips_result['compliant'] else 'No'}")
    print(f"⚠️ Violations: {len(fips_result['violations'])}")
    print(f"💡 Recommendations: {len(fips_result['recommendations'])}")
    print(f"🛡️ Security Score: {fips_result['security_assessment'].get('overall_security_score', 'N/A')}")
    print(f"📋 Certification Impact: {fips_result['certification_impact']}")
    
    if fips_result['violations']:
        print("\n🚨 Violations Found:")
        for i, violation in enumerate(fips_result['violations'][:3], 1):  # Show first 3
            print(f"  {i}. [{violation['severity'].upper()}] {violation['message']}")
            if violation.get('fix_suggestion'):
                print(f"     💡 Fix: {violation['fix_suggestion']}")
    
    # Example 4: Multi-platform Build
    print("\n🏗️ Example 4: Multi-platform Build")
    print("-" * 35)
    
    build_result = await orchestration_main.mcp_server.tools["build_openssl_for_platforms"](
        platforms=["linux-gcc11", "windows-msvc193", "macos-arm64"],
        fips_enabled=True
    )
    
    print(f"✅ Build Process: {'Success' if build_result['success'] else 'Failed'}")
    print(f"🖥️ Platforms: {', '.join(build_result['platforms'])}")
    print(f"⏱️ Total Build Time: {build_result['total_build_time']:.2f}s")
    print(f"🔒 FIPS Enabled: {build_result['fips_enabled']}")
    
    if build_result['build_results']:
        print("\n📊 Build Results by Platform:")
        for result in build_result['build_results']:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['platform']}: {result['build_time']:.2f}s")
            if result['artifacts']:
                print(f"    📦 Artifacts: {', '.join(result['artifacts'])}")
            if result['errors']:
                print(f"    ❌ Errors: {len(result['errors'])}")
    
    # Example 5: Create Release
    print("\n📦 Example 5: Creating OpenSSL Release")
    print("-" * 40)
    
    release_result = await orchestration_main.mcp_server.tools["create_openssl_release"](
        version="1.0.0",
        platforms=["linux-gcc11", "windows-msvc193", "macos-arm64"],
        fips_enabled=True
    )
    
    print(f"✅ Release Creation: {'Success' if release_result['success'] else 'Failed'}")
    print(f"🏷️ Version: {release_result['version']}")
    print(f"🖥️ Platforms: {', '.join(release_result['platforms'])}")
    print(f"📦 Artifacts: {len(release_result['artifacts'])}")
    
    if release_result['artifacts']:
        print("\n📋 Release Artifacts:")
        for artifact in release_result['artifacts'][:5]:  # Show first 5
            print(f"  📄 {artifact}")
    
    # Example 6: Skills Catalog
    print("\n🔧 Example 6: OpenSSL Skills Catalog")
    print("-" * 40)
    
    skills_result = await orchestration_main.mcp_server.tools["get_openssl_skills_catalog"]()
    
    print(f"✅ Skills Catalog: {'Success' if skills_result['success'] else 'Failed'}")
    print(f"📚 Total Skills: {skills_result['total_count']}")
    
    if skills_result['categories']:
        print("\n📊 Skills by Category:")
        for category, count in skills_result['categories'].items():
            print(f"  {category.title()}: {count}")
    
    if skills_result['skills']:
        print("\n🔧 Available Skills:")
        for skill in skills_result['skills'][:5]:  # Show first 5
            print(f"  • {skill['name']} ({skill['skill_type']})")
            print(f"    Triggers: {', '.join(skill['triggers'][:3])}...")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 OpenSSL Tools Orchestration Example Complete!")
    print("=" * 50)
    
    print("\n📋 Summary of Generated Artifacts:")
    print("  📁 Project structure with all necessary directories")
    print("  ⚙️ GitHub Actions workflows for CI/CD")
    print("  🏗️ Multi-platform build configurations")
    print("  🧪 Comprehensive testing framework")
    print("  🔒 FIPS compliance validation system")
    print("  📦 Release management and artifact creation")
    print("  🔧 Skills-enabled automation and orchestration")
    
    print("\n🚀 Next Steps:")
    print("  1. Review the generated project structure")
    print("  2. Customize the GitHub Actions workflows")
    print("  3. Configure FIPS compliance requirements")
    print("  4. Set up your development environment")
    print("  5. Start developing with Skills-enabled assistance!")

async def example_skills_integration():
    """Example of Skills integration and composition."""
    
    print("\n🔧 Skills Integration Example")
    print("=" * 40)
    
    # Initialize orchestration
    orchestration_main = OpenSSLOrchestrationMain()
    
    # Create a project context that will trigger multiple skills
    context = OpenSSLProjectContext(
        project_type=OpenSSLProjectType.OPENSSL_TOOLS,
        repository_url="https://github.com/sparesparrow/openssl-tools",
        target_platforms=[BuildPlatform.LINUX_GCC11, BuildPlatform.MACOS_ARM64],
        fips_required=True,
        ci_cd_enabled=True,
        testing_framework="pytest"
    )
    
    # Convert to Skills registry context
    from mcp_project_orchestrator.skills_registry import ProjectContext
    
    skills_context = ProjectContext(
        project_idea="OpenSSL tools with FIPS compliance and CI/CD automation",
        project_type=context.project_type.value,
        technologies=context.build_tools,
        requirements=[
            "FIPS 140-3 compliance",
            "Multi-platform build support",
            "Comprehensive testing framework",
            "CI/CD pipeline automation",
            "Security validation and scanning"
        ],
        constraints={"fips_required": context.fips_required},
        objectives=["Security", "Performance", "Compliance", "Maintainability"],
        security_level=context.security_level,
        fips_required=context.fips_required,
        platform_targets=[p.value for p in context.target_platforms]
    )
    
    # Discover and compose skills
    skill_composition = await orchestration_main.openssl_orchestrator.skills_registry.discover_and_compose_skills(skills_context)
    
    print(f"🔍 Discovered Skills: {len(skill_composition.skills)}")
    print(f"📋 Execution Order: {skill_composition.execution_order}")
    print(f"🔗 Dependencies: {len(skill_composition.dependency_graph)}")
    print(f"⏱️ Estimated Time: {skill_composition.estimated_execution_time}s")
    print(f"🎯 Token Budget: {skill_composition.total_token_budget}")
    
    print("\n🔧 Skills Details:")
    for skill in skill_composition.skills:
        print(f"  • {skill.name}")
        print(f"    Type: {skill.skill_type.value}")
        print(f"    Priority: {skill.priority.value}")
        print(f"    Triggers: {', '.join(skill.triggers[:3])}...")
        print(f"    Verification Required: {skill.verification_required}")
        print()

def main():
    """Main function to run the examples."""
    
    print("🚀 OpenSSL Tools Orchestration Examples")
    print("=" * 50)
    print("This example demonstrates the comprehensive OpenSSL Tools")
    print("Orchestration system with Agent Skills integration.")
    print()
    
    try:
        # Run the main orchestration example
        asyncio.run(example_openssl_tools_orchestration())
        
        # Run the skills integration example
        asyncio.run(example_skills_integration())
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Example interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running example: {e}")
        logger.exception("Example execution failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())