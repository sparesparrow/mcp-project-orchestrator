#!/bin/bash
set -e

echo "🧪 Testing OpenSSL + AI Integration"
echo "=================================="

# Test 1: Create OpenSSL consumer project
echo "📋 Test 1: Create OpenSSL consumer project"
mcp-orchestrator create-openssl-project \
  --project-name test-crypto-app \
  --openssl-version 3.4.1 \
  --deployment-target general \
  --author-name "Test Developer"

cd test-crypto-app

# Test 2: Deploy Cursor configuration
echo "🤖 Test 2: Deploy Cursor configuration"
mcp-orchestrator deploy-cursor --project-type openssl --force

# Test 3: Build project
echo "🔨 Test 3: Build project"
conan remote add sparesparrow-conan \
  https://conan.cloudsmith.io/sparesparrow-conan/openssl-conan/ \
  --force

conan install . --build=missing
cmake --preset conan-default
cmake --build --preset conan-release

# Test 4: Run application
echo "🚀 Test 4: Run application"
./build/Release/test-crypto-app

echo "✅ All tests passed!"
cd ..
