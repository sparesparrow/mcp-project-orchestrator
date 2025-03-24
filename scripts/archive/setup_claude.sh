#!/bin/bash
# Wrapper script for setup_claude_desktop.py that handles Python environment issues

# Find a suitable Python interpreter
find_python() {
    # Try Python 3 first
    if command -v python3 &> /dev/null; then
        echo "python3"
        return
    fi
    
    # Then try just "python"
    if command -v python &> /dev/null; then
        echo "python"
        return
    fi
    
    # Check for a virtual environment in the project
    if [ -f "venv/bin/python" ]; then
        echo "venv/bin/python"
        return
    fi
    
    # No Python found
    echo ""
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/setup_claude_desktop.py"

# Find Python
PYTHON=$(find_python)

if [ -z "$PYTHON" ]; then
    echo "Error: Could not find a Python interpreter. Please install Python 3 and try again."
    exit 1
fi

# Clean environment variables to avoid conflicts
unset PYTHONHOME
unset PYTHONPATH

echo "Using Python interpreter: $PYTHON"
echo "Running setup script: $PYTHON_SCRIPT"
echo "Arguments: $*"
echo 

# Run the Python script with the clean environment
$PYTHON "$PYTHON_SCRIPT" "$@" 