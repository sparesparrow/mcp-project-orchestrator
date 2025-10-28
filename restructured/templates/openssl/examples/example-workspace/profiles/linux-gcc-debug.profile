[settings]
os=Linux
arch=x86_64
compiler=gcc
compiler.version=11
compiler.libcxx=libstdc++11
build_type=Debug

[options]
*:shared=True

[conf]
tools.system.package_manager:mode=install
tools.system.package_manager:sudo=True

[env]
# Cursor configuration
CURSOR_CONFIG_PATH=/workspace/example-workspace/.cursor
MCP_ORCHESTRATOR_PLATFORM=linux
MCP_ORCHESTRATOR_ARCHITECTURE=x86_64
MCP_ORCHESTRATOR_USER=developer
MCP_ORCHESTRATOR_HOME=/home/developer
MCP_ORCHESTRATOR_CI=false

# OpenSSL specific
OPENSSL_ROOT_DIR=/usr/local
PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Debug build flags
CFLAGS=-Wall -Wextra -Werror -g -O0
CXXFLAGS=-Wall -Wextra -Werror -g -O0