#!/bin/bash
"""
Build all Conan packages for the MCP Project Orchestrator ecosystem.

This script builds all packages in the correct dependency order
and creates a complete package repository.
"""

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BUILD_DIR="build"
PACKAGE_DIR="packages"
CONAN_REMOTE="mcp-orchestrator"
CONAN_USER="sparesparrow"
CONAN_CHANNEL="stable"

# Build profiles
PROFILES=(
    "linux-gcc11-release"
    "linux-gcc11-debug"
    "windows-msvc193-release"
    "windows-msvc193-debug"
    "macos-clang-release"
    "macos-clang-debug"
)

# Package build order (dependencies first)
PACKAGES=(
    "openssl-fips-validator"
    "agent-skills-framework"
    "openssl-tools-orchestrator"
    "openssl-workflows"
    "aws-sip-trunk"
    "automotive-camera-system"
    "printcast-agent"
    "elevenlabs-agents"
    "mcp-project-orchestrator"
    "mcp-project-orchestrator-complete"
)

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date +'%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# Function to check if Conan is installed
check_conan() {
    if ! command -v conan &> /dev/null; then
        print_status $RED "Conan is not installed. Please install Conan first."
        exit 1
    fi
    
    print_status $GREEN "Conan found: $(conan --version)"
}

# Function to setup Conan configuration
setup_conan() {
    print_status $BLUE "Setting up Conan configuration..."
    
    # Create Conan profile if it doesn't exist
    if ! conan profile show default &> /dev/null; then
        conan profile detect --force
    fi
    
    # Add remote if it doesn't exist
    if ! conan remote list | grep -q "$CONAN_REMOTE"; then
        conan remote add "$CONAN_REMOTE" "https://api.bintray.com/conan/sparesparrow/mcp-orchestrator"
    fi
    
    print_status $GREEN "Conan configuration complete"
}

# Function to create build profiles
create_profiles() {
    print_status $BLUE "Creating build profiles..."
    
    mkdir -p profiles
    
    # Linux GCC 11 Release
    cat > profiles/linux-gcc11-release << EOF
[settings]
os=Linux
arch=x86_64
compiler=gcc
compiler.version=11
compiler.libcxx=libstdc++11
build_type=Release

[options]
*:shared=False
*:fPIC=True

[conf]
tools.cmake.cmake_layout:build_folder_vars=['settings.compiler.version']
EOF

    # Linux GCC 11 Debug
    cat > profiles/linux-gcc11-debug << EOF
[settings]
os=Linux
arch=x86_64
compiler=gcc
compiler.version=11
compiler.libcxx=libstdc++11
build_type=Debug

[options]
*:shared=False
*:fPIC=True

[conf]
tools.cmake.cmake_layout:build_folder_vars=['settings.compiler.version']
EOF

    # Windows MSVC 193 Release
    cat > profiles/windows-msvc193-release << EOF
[settings]
os=Windows
arch=x86_64
compiler=msvc
compiler.version=193
compiler.runtime=dynamic
build_type=Release

[options]
*:shared=False

[conf]
tools.cmake.cmake_layout:build_folder_vars=['settings.compiler.version']
EOF

    # Windows MSVC 193 Debug
    cat > profiles/windows-msvc193-debug << EOF
[settings]
os=Windows
arch=x86_64
compiler=msvc
compiler.version=193
compiler.runtime=dynamic
build_type=Debug

[options]
*:shared=False

[conf]
tools.cmake.cmake_layout:build_folder_vars=['settings.compiler.version']
EOF

    # macOS Clang Release
    cat > profiles/macos-clang-release << EOF
[settings]
os=Macos
arch=x86_64
compiler=apple-clang
compiler.version=15
compiler.libcxx=libc++
build_type=Release

[options]
*:shared=False
*:fPIC=True

[conf]
tools.cmake.cmake_layout:build_folder_vars=['settings.compiler.version']
EOF

    # macOS Clang Debug
    cat > profiles/macos-clang-debug << EOF
[settings]
os=Macos
arch=x86_64
compiler=apple-clang
compiler.version=15
compiler.libcxx=libc++
build_type=Debug

[options]
*:shared=False
*:fPIC=True

[conf]
tools.cmake.cmake_layout:build_folder_vars=['settings.compiler.version']
EOF

    print_status $GREEN "Build profiles created"
}

# Function to build a single package
build_package() {
    local package=$1
    local profile=$2
    local build_type=$(echo $profile | cut -d'-' -f3)
    
    print_status $YELLOW "Building $package with profile $profile..."
    
    local package_path="recipes/$package"
    if [ ! -d "$package_path" ]; then
        print_status $RED "Package directory not found: $package_path"
        return 1
    fi
    
    # Build the package
    conan create "$package_path" "$CONAN_USER/$CONAN_CHANNEL" \
        --profile="profiles/$profile" \
        --build=missing \
        --build=cascade \
        --output-folder="$BUILD_DIR" \
        --package-folder="$PACKAGE_DIR"
    
    if [ $? -eq 0 ]; then
        print_status $GREEN "Successfully built $package with profile $profile"
    else
        print_status $RED "Failed to build $package with profile $profile"
        return 1
    fi
}

# Function to build all packages
build_all_packages() {
    print_status $BLUE "Building all packages..."
    
    local failed_packages=()
    
    for profile in "${PROFILES[@]}"; do
        print_status $BLUE "Building with profile: $profile"
        
        for package in "${PACKAGES[@]}"; do
            if ! build_package "$package" "$profile"; then
                failed_packages+=("$package:$profile")
            fi
        done
    done
    
    if [ ${#failed_packages[@]} -eq 0 ]; then
        print_status $GREEN "All packages built successfully!"
    else
        print_status $RED "Failed packages:"
        for failed in "${failed_packages[@]}"; do
            echo "  - $failed"
        done
        return 1
    fi
}

# Function to upload packages to remote
upload_packages() {
    print_status $BLUE "Uploading packages to remote..."
    
    for package in "${PACKAGES[@]}"; do
        print_status $YELLOW "Uploading $package..."
        conan upload "$package" --all --remote="$CONAN_REMOTE" --confirm
    done
    
    print_status $GREEN "All packages uploaded successfully!"
}

# Function to create package index
create_package_index() {
    print_status $BLUE "Creating package index..."
    
    cat > "$PACKAGE_DIR/index.json" << EOF
{
    "name": "MCP Project Orchestrator Package Repository",
    "version": "0.2.0",
    "description": "Complete package repository for MCP Project Orchestrator ecosystem",
    "packages": [
EOF

    local first=true
    for package in "${PACKAGES[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$PACKAGE_DIR/index.json"
        fi
        
        cat >> "$PACKAGE_DIR/index.json" << EOF
        {
            "name": "$package",
            "version": "0.2.0",
            "description": "Package description for $package",
            "profiles": [
EOF
        
        local profile_first=true
        for profile in "${PROFILES[@]}"; do
            if [ "$profile_first" = true ]; then
                profile_first=false
            else
                echo "," >> "$PACKAGE_DIR/index.json"
            fi
            echo "                \"$profile\"" >> "$PACKAGE_DIR/index.json"
        done
        
        echo "            ]" >> "$PACKAGE_DIR/index.json"
        echo "        }" >> "$PACKAGE_DIR/index.json"
    done
    
    cat >> "$PACKAGE_DIR/index.json" << EOF
    ],
    "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "conan_version": "$(conan --version | cut -d' ' -f3)"
}
EOF

    print_status $GREEN "Package index created"
}

# Function to run tests
run_tests() {
    print_status $BLUE "Running package tests..."
    
    for package in "${PACKAGES[@]}"; do
        print_status $YELLOW "Testing $package..."
        
        # Test package installation
        conan install "$package/$CONAN_USER@$CONAN_CHANNEL" \
            --profile="profiles/linux-gcc11-release" \
            --build=missing
        
        if [ $? -eq 0 ]; then
            print_status $GREEN "Package $package test passed"
        else
            print_status $RED "Package $package test failed"
            return 1
        fi
    done
    
    print_status $GREEN "All package tests passed!"
}

# Main function
main() {
    print_status $BLUE "Starting MCP Project Orchestrator package build process..."
    
    # Create directories
    mkdir -p "$BUILD_DIR" "$PACKAGE_DIR" profiles
    
    # Check prerequisites
    check_conan
    
    # Setup Conan
    setup_conan
    
    # Create profiles
    create_profiles
    
    # Build all packages
    build_all_packages
    
    # Run tests
    run_tests
    
    # Create package index
    create_package_index
    
    # Upload packages (optional)
    if [ "${1:-}" = "--upload" ]; then
        upload_packages
    fi
    
    print_status $GREEN "Build process completed successfully!"
    print_status $BLUE "Packages available in: $PACKAGE_DIR"
    print_status $BLUE "Build artifacts in: $BUILD_DIR"
}

# Run main function
main "$@"