#!/usr/bin/env python3
"""
Create example workspace zip artifact.

This script creates a zip file containing an example OpenSSL workspace
with Cursor AI configuration and Conan profiles.
"""

import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime


def create_example_workspace_zip():
    """Create example workspace zip file."""
    
    # Get script directory
    script_dir = Path(__file__).parent
    examples_dir = script_dir.parent / "examples"
    workspace_dir = examples_dir / "example-workspace"
    
    # Handle nested directory structure
    if not workspace_dir.exists():
        # Try alternative path
        workspace_dir = script_dir.parent.parent / "examples" / "example-workspace"
    
    if not workspace_dir.exists():
        print(f"❌ Example workspace directory not found: {workspace_dir}")
        return False
    
    # Create zip file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"openssl-cursor-example-workspace-{timestamp}.zip"
    zip_path = script_dir.parent / zip_filename
    
    print(f"📦 Creating example workspace zip: {zip_filename}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files from workspace directory
        for file_path in workspace_dir.rglob('*'):
            if file_path.is_file():
                # Calculate relative path from workspace directory
                rel_path = file_path.relative_to(workspace_dir)
                zipf.write(file_path, rel_path)
                print(f"  📄 {rel_path}")
    
    print(f"✅ Example workspace zip created: {zip_path}")
    print(f"   Size: {zip_path.stat().st_size / 1024:.1f} KB")
    
    return True


def main():
    """Main function."""
    print("🚀 Creating OpenSSL Cursor Example Workspace")
    print("   This zip contains a complete example workspace showing")
    print("   how Cursor AI configuration maps to Conan profiles.")
    print()
    
    success = create_example_workspace_zip()
    
    if success:
        print()
        print("📋 Example workspace contents:")
        print("   - .cursor/ directory with AI configuration")
        print("   - profiles/ directory with Conan profiles")
        print("   - Complete OpenSSL C++ project")
        print("   - README.md with mapping documentation")
        print("   - CMakeLists.txt and conanfile.py")
        print()
        print("🎯 Usage:")
        print("   1. Extract the zip file")
        print("   2. Read README.md for detailed instructions")
        print("   3. Run: deploy-cursor --project-type openssl")
        print("   4. Run: conan profile detect")
        print("   5. Build with: conan install . && cmake --build build/")
    else:
        print("❌ Failed to create example workspace zip")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())