#!/usr/bin/env bash

# Complete project orchestration setup for Cursor on Linux.
# - Installs core tooling (git, curl, jq, Node via nvm, Python, Podman)
# - Configures .cursor MCP servers, rules, tools, hooks, deeplinks
# - Scaffolds background agents and webhooks (FastAPI)
# - Adds GitHub Actions workflows (CI, docs, code review)
# - Generates multi-language templates (MCP servers: Py/TS/C++, client, web, AWS, Docker, devcontainer,
#   C++ ESP32, C++ with Conan, Android Kotlin containerized builder)
# - Safe to run multiple times; idempotent where possible

set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_NAME="$(basename "$0")"
START_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ----------------------------- Utilities ------------------------------------

log() { printf "[setup][%s] %s\n" "$(date +%H:%M:%S)" "$*"; }
warn() { printf "\033[33m[warn]\033[0m %s\n" "$*"; }
err() { printf "\033[31m[err ]\033[0m %s\n" "$*" 1>&2; }
die() { err "$*"; exit 1; }
have_cmd() { command -v "$1" >/dev/null 2>&1; }
json_get() { jq -r "$1" "$CONFIG_PATH" 2>/dev/null; }

SUDO=""
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  if have_cmd sudo; then SUDO="sudo -n"; else warn "sudo not found; attempting without elevated privileges"; fi
fi

require_or_install_pkg() {
  # Best-effort package installation across distros. Usage: require_or_install_pkg pkgname [cmd_to_check]
  local pkg="$1"; shift || true
  local check_cmd="${1:-}";
  if [ -n "$check_cmd" ] && have_cmd "$check_cmd"; then return 0; fi
  if [ -n "$check_cmd" ] && [ -x "$check_cmd" ]; then return 0; fi

  if [ -r /etc/os-release ]; then . /etc/os-release; fi

  if have_cmd apt-get; then
    $SUDO DEBIAN_FRONTEND=noninteractive apt-get update -y || true
    $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg" || warn "apt-get install $pkg failed"
  elif have_cmd dnf; then
    $SUDO dnf install -y "$pkg" || warn "dnf install $pkg failed"
  elif have_cmd yum; then
    $SUDO yum install -y "$pkg" || warn "yum install $pkg failed"
  elif have_cmd pacman; then
    $SUDO pacman -Sy --noconfirm "$pkg" || warn "pacman install $pkg failed"
  elif have_cmd zypper; then
    $SUDO zypper install -y "$pkg" || warn "zypper install $pkg failed"
  elif have_cmd apk; then
    $SUDO apk add --no-cache "$pkg" || warn "apk add $pkg failed"
  else
    warn "Unsupported package manager; could not install $pkg"
  fi
}

install_base_packages() {
  log "Installing base packages (git, curl, wget, jq, build tools, Python, Podman)"

  # Core CLI
  require_or_install_pkg git git
  require_or_install_pkg curl curl
  require_or_install_pkg wget wget
  require_or_install_pkg jq jq
  require_or_install_pkg ca-certificates
  require_or_install_pkg unzip unzip
  require_or_install_pkg tar tar
  require_or_install_pkg xz-utils || true

  # Build toolchain
  if have_cmd apt-get; then
    require_or_install_pkg build-essential
    require_or_install_pkg cmake cmake
    require_or_install_pkg ninja-build ninja
    require_or_install_pkg pkg-config pkg-config
  else
    require_or_install_pkg gcc gcc || true
    require_or_install_pkg g++ g++ || true
    require_or_install_pkg cmake cmake || true
    require_or_install_pkg ninja ninja || true
    require_or_install_pkg pkgconf pkgconf || require_or_install_pkg pkg-config pkg-config || true
  fi

  # Python
  require_or_install_pkg python3 python3
  if have_cmd apt-get; then
    require_or_install_pkg python3-venv || true
    require_or_install_pkg python3-pip || true
    require_or_install_pkg pipx || true
  else
    require_or_install_pkg python3-pip || true
  fi

  # Containers: honor container.prefer from JSON
  local prefer="$(json_get '.container.prefer')"
  if [ "$prefer" = "docker" ]; then
    # Prefer Docker engine when requested
    if have_cmd apt-get; then
      require_or_install_pkg docker.io docker || warn "Failed to install docker.io"
    elif have_cmd dnf; then
      require_or_install_pkg docker docker || require_or_install_pkg moby-engine docker || true
    fi
    if have_cmd docker; then
      log "Docker is available"
    else
      warn "Docker not available; container preference is docker but installation may have failed"
    fi
  else
    # Default/Podman path
    require_or_install_pkg podman podman || warn "Podman not installed; containerization features may be limited"
    # Provide docker compatibility shim if docker client missing and podman exists
    if have_cmd podman && ! have_cmd docker; then
      if [ ! -x /usr/local/bin/docker ]; then
        log "Creating docker -> podman shim at /usr/local/bin/docker"
        echo '#!/usr/bin/env bash' | $SUDO tee /usr/local/bin/docker >/dev/null
        echo 'exec podman "$@"' | $SUDO tee -a /usr/local/bin/docker >/dev/null
        $SUDO chmod +x /usr/local/bin/docker || true
      fi
    fi
  fi

  # Optional: docker-compose replacement for Podman
  if ! have_cmd podman-compose; then
    if have_cmd pipx; then pipx install podman-compose || true; fi
  fi
}

install_node_via_nvm() {
  if have_cmd node; then
    log "Node.js present: $(node -v)"
  else
    log "Installing Node.js (LTS) via nvm"
    export NVM_DIR="$HOME/.nvm"
    mkdir -p "$NVM_DIR"
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    # shellcheck source=/dev/null
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm install --lts
    nvm alias default 'lts/*'
  fi

  if have_cmd corepack; then
    corepack enable || true
    corepack prepare pnpm@latest --activate || true
  else
    npm install -g pnpm yarn || true
  fi
}

install_python_tools() {
  log "Ensuring pip, pipx, and venv availability"
  if ! have_cmd pipx; then
    if have_cmd python3; then python3 -m pip install --user -q pipx || true; fi
    if have_cmd pipx; then pipx ensurepath || true; fi
  fi
}

create_dirs() {
  WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
  if [ ! -d "$WORKSPACE_ROOT" ]; then WORKSPACE_ROOT="$(pwd)"; fi
  export WORKSPACE_ROOT
  log "Using WORKSPACE_ROOT=$WORKSPACE_ROOT"

  mkdir -p "$WORKSPACE_ROOT/.cursor/tools" \
           "$WORKSPACE_ROOT/.cursor/hooks" \
           "$WORKSPACE_ROOT/.cursor/webhooks" \
           "$WORKSPACE_ROOT/.cursor/agents" \
           "$WORKSPACE_ROOT/scripts" \
           "$WORKSPACE_ROOT/servers/python-mcp" \
           "$WORKSPACE_ROOT/servers/ts-mcp/src" \
           "$WORKSPACE_ROOT/servers/cpp-mcp/src" \
           "$WORKSPACE_ROOT/client/mcp-client/src" \
           "$WORKSPACE_ROOT/services/background-agent" \
           "$WORKSPACE_ROOT/.github/workflows" \
           "$WORKSPACE_ROOT/templates" \
           "$WORKSPACE_ROOT/infra/aws/terraform" \
           "$WORKSPACE_ROOT/devcontainer" \
           "$WORKSPACE_ROOT/web"
}

write_file() {
  # write_file <path> <mode> <<'EOF'
  local path="$1"; shift
  local mode="$1"; shift
  $SUDO mkdir -p "$(dirname "$path")"
  # shellcheck disable=SC2094
  cat >"$path"
  $SUDO chmod "$mode" "$path" || true
}

setup_cursor_configs() {
  if [ "$(json_get '.enable.cursorConfigs')" != "true" ]; then return 0; fi
  log "Writing .cursor configuration (MCP servers, tools, rules, hooks, deeplinks)"

  # Build MCP servers config from JSON flags
  local mcpEntries="{}"
  local py_port
  py_port="$(json_get '.ports.pyMcpPort')" || py_port="8765"
  if [ -z "$py_port" ] || [ "$py_port" = "null" ]; then py_port="8765"; fi
  local ts_port
  ts_port="$(json_get '.ports.tsMcpPort')" || ts_port="8766"
  if [ -z "$ts_port" ] || [ "$ts_port" = "null" ]; then ts_port="8766"; fi
  if [ "$(json_get '.enable.pythonMcp')" = "true" ]; then
    mcpEntries=$(jq --arg port "$py_port" '. + {"mcp-python": {"command":"bash","args":["-lc","python3 servers/python-mcp/main.py"],"env":{"PY_MCP_PORT": $port}}}' <<<"$mcpEntries")
  fi
  if [ "$(json_get '.enable.tsMcp')" = "true" ]; then
    mcpEntries=$(jq --arg port "$ts_port" '. + {"mcp-typescript": {"command":"bash","args":["-lc","node servers/ts-mcp/dist/index.js"],"env":{"TS_MCP_PORT": $port}}}' <<<"$mcpEntries")
  fi
  if [ "$(json_get '.enable.cppMcp')" = "true" ]; then
    mcpEntries=$(jq '. + {"mcp-cpp": {"command":"bash","args":["-lc","./servers/cpp-mcp/build/mcp_server"],"env":{}}}' <<<"$mcpEntries")
  fi
  jq -n --argjson servers "$mcpEntries" '{servers: $servers}' > "$WORKSPACE_ROOT/.cursor/mcp.json"

  if [ "$(json_get '.tools.largeCodebases.enabled')" = "true" ]; then
    jq -n \
      --argjson enabled true \
      --argjson exclude "$(json_get '.tools.largeCodebases.exclude')" \
      --argjson maxFileSizeMB "$(json_get '.tools.largeCodebases.maxFileSizeMB')" \
      '{enabled: $enabled, exclude: $exclude, maxFileSizeMB: $maxFileSizeMB}' \
      > "$WORKSPACE_ROOT/.cursor/tools/large-codebases.json"
  fi

  if [ "$(json_get '.tools.mermaid.enabled')" = "true" ]; then
    jq -n '{enabled: true}' > "$WORKSPACE_ROOT/.cursor/tools/mermaid-diagrams.json"
  fi

  write_file "$WORKSPACE_ROOT/.cursor/rules.json" 0644 <<'JSON'
{
  "rules": [
    {"pattern": "**/*.py", "instructions": "Follow PEP 8, PEP 257. Use type hints."},
    {"pattern": "**/*.{ts,tsx}", "instructions": "Use strict TypeScript. Prefer explicit types for exports."},
    {"pattern": "**/*.cpp", "instructions": "Use modern C++17+, CMake targets, no raw new/delete."}
  ]
}
JSON

  write_file "$WORKSPACE_ROOT/.cursor/hooks/agent-hooks.json" 0644 <<'JSON'
{
  "preTask": [
    {"type": "log", "level": "info", "message": "Starting task"}
  ],
  "postTask": [
    {"type": "log", "level": "info", "message": "Task complete"}
  ]
}
JSON

  local agent_host="$(json_get '.backgroundAgent.host')"
  local agent_port="$(json_get '.backgroundAgent.port')"
  jq -n \
    --arg url "http://${agent_host}:${agent_port}/webhooks/cursor" \
    '{webhooks: [{name: "background-agent", url: $url, events: ["task.created","task.updated","run.completed"]}]}' \
    > "$WORKSPACE_ROOT/.cursor/webhooks/webhooks.json"

  jq -n \
    --arg baseUrl "http://${agent_host}:${agent_port}" \
    '{agents: [{name: "default", baseUrl: $baseUrl, enabled: true}]}' \
    > "$WORKSPACE_ROOT/.cursor/agents/background-agent.json"
}

scaffold_python_mcp_server() {
  if [ "$(json_get '.enable.pythonMcp')" != "true" ]; then return 0; fi
  log "Scaffolding Python MCP server template"
  write_file "$WORKSPACE_ROOT/servers/python-mcp/pyproject.toml" 0644 <<'TOML'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "python-mcp-server"
version = "0.1.0"
description = "Example Python MCP server"
requires-python = ">=3.9"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0"
]
TOML

  write_file "$WORKSPACE_ROOT/servers/python-mcp/main.py" 0755 <<'PY'
#!/usr/bin/env python3
"""
Minimal Python MCP server placeholder.

This is a scaffold to be adapted to a real MCP implementation. It starts a FastAPI
HTTP app to demonstrate a background service that could receive MCP-like requests.

Replace with an actual MCP server according to the latest Cursor MCP docs.
"""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Python MCP Server (placeholder)")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> JSONResponse:
    return JSONResponse({"message": "Replace with real MCP protocol server."})


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PY_MCP_PORT", "8765"))
    uvicorn.run(app, host="127.0.0.1", port=port)
PY
}

scaffold_ts_mcp_server() {
  if [ "$(json_get '.enable.tsMcp')" != "true" ]; then return 0; fi
  log "Scaffolding TypeScript MCP server template"
  write_file "$WORKSPACE_ROOT/servers/ts-mcp/package.json" 0644 <<'JSON'
{
  "name": "ts-mcp-server",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "tsc -p .",
    "start": "node dist/index.js"
  },
  "devDependencies": {
    "typescript": "^5.6.3"
  },
  "dependencies": {}
}
JSON

  write_file "$WORKSPACE_ROOT/servers/ts-mcp/tsconfig.json" 0644 <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true
  }
}
JSON

  write_file "$WORKSPACE_ROOT/servers/ts-mcp/src/index.ts" 0644 <<'TS'
/*
  Minimal TypeScript MCP server placeholder.
  Replace with a real MCP server per Cursor docs.
*/
import http from "node:http";

const server = http.createServer((_req, res) => {
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify({ message: "Replace with real MCP server." }));
});

const port = Number(process.env.TS_MCP_PORT ?? 8766);
server.listen(port, "127.0.0.1", () => {
  // eslint-disable-next-line no-console
  console.log(`TS MCP placeholder listening on http://127.0.0.1:${port}`);
});
TS
}

scaffold_cpp_mcp_server() {
  if [ "$(json_get '.enable.cppMcp')" != "true" ]; then return 0; fi
  log "Scaffolding C++ MCP server template"
  write_file "$WORKSPACE_ROOT/servers/cpp-mcp/CMakeLists.txt" 0644 <<'CMAKE'
cmake_minimum_required(VERSION 3.16)
project(cpp_mcp_server LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(mcp_server src/main.cpp)
CMAKE

  write_file "$WORKSPACE_ROOT/servers/cpp-mcp/src/main.cpp" 0644 <<'CPP'
#include <iostream>

int main() {
  std::cout << "Replace with real MCP server (C++)." << std::endl;
  return 0;
}
CPP

  write_file "$WORKSPACE_ROOT/servers/cpp-mcp/build.sh" 0755 <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -rf build && mkdir -p build && cd build
cmake .. -G Ninja || cmake ..
cmake --build . --config Release
SH
}

scaffold_mcp_client_ts() {
  if [ "$(json_get '.enable.mcpClient')" != "true" ]; then return 0; fi
  log "Scaffolding MCP client (TypeScript) template"
  write_file "$WORKSPACE_ROOT/client/mcp-client/package.json" 0644 <<'JSON'
{
  "name": "mcp-client",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "tsc -p .",
    "start": "node dist/index.js"
  },
  "devDependencies": {
    "typescript": "^5.6.3"
  },
  "dependencies": {}
}
JSON

  write_file "$WORKSPACE_ROOT/client/mcp-client/tsconfig.json" 0644 <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true
  }
}
JSON

  write_file "$WORKSPACE_ROOT/client/mcp-client/src/index.ts" 0644 <<'TS'
/* Placeholder MCP client. Replace with actual MCP client logic. */
// eslint-disable-next-line no-console
console.log("MCP client placeholder");
TS
}

scaffold_background_agent() {
  if [ "$(json_get '.enable.backgroundAgent')" != "true" ]; then return 0; fi
  log "Scaffolding background agent + webhooks (FastAPI)"
  write_file "$WORKSPACE_ROOT/services/background-agent/requirements.txt" 0644 <<'REQ'
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
REQ

  write_file "$WORKSPACE_ROOT/services/background-agent/main.py" 0755 <<'PY'
#!/usr/bin/env python3
"""
Background agent + webhook receiver (FastAPI).

Endpoints:
  - GET /health
  - POST /webhooks/cursor (generic webhook entry)
  - GET /api/events (example endpoint)

Run locally:
  uvicorn main:app --host 127.0.0.1 --port 8088 --reload
"""
from __future__ import annotations

from typing import Any, Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Background Agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/webhooks/cursor")
async def cursor_webhook(request: Request) -> JSONResponse:
    payload: Dict[str, Any] = await request.json()
    # TODO: handle events appropriately
    return JSONResponse({"received": True, "keys": list(payload.keys())})


@app.get("/api/events")
def list_events() -> dict:
    return {"events": []}
PY

  write_file "$WORKSPACE_ROOT/scripts/run-background-agent.sh" 0755 <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1
CONFIG_PATH="${CONFIG_PATH:-$(pwd)/config/project_orchestration.json}"
HOST="127.0.0.1"
PORT="8088"
if command -v jq >/dev/null 2>&1 && [ -f "$CONFIG_PATH" ]; then
  HOST="$(jq -r '.backgroundAgent.host' "$CONFIG_PATH" 2>/dev/null || echo "$HOST")"
  PORT="$(jq -r '.backgroundAgent.port' "$CONFIG_PATH" 2>/dev/null || echo "$PORT")"
fi
python3 -m venv .venv 2>/dev/null || true
. .venv/bin/activate
python -m pip install -U pip
pip install -r services/background-agent/requirements.txt
exec uvicorn services.background-agent.main:app --host "$HOST" --port "$PORT" --reload
SH
}

scaffold_github_actions() {
  if [ "$(json_get '.enable.githubActions')" != "true" ]; then return 0; fi
  log "Adding GitHub Actions workflows (CI, docs, code review)"

  write_file "$WORKSPACE_ROOT/.github/workflows/ci.yml" 0644 <<'YML'
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Node deps (if any)
        run: |
          if [ -f servers/ts-mcp/package.json ]; then npm ci --prefix servers/ts-mcp || true; fi
          if [ -f client/mcp-client/package.json ]; then npm ci --prefix client/mcp-client || true; fi
      - name: Install Python deps (if any)
        run: |
          python -m pip install -U pip
          if [ -f servers/python-mcp/pyproject.toml ]; then pip install -e servers/python-mcp || true; fi
          if [ -f services/background-agent/requirements.txt ]; then pip install -r services/background-agent/requirements.txt || true; fi
      - name: Build TS artifacts
        run: |
          if [ -f servers/ts-mcp/package.json ]; then npm --prefix servers/ts-mcp run build || true; fi
          if [ -f client/mcp-client/package.json ]; then npm --prefix client/mcp-client run build || true; fi
      - name: C++ build
        run: |
          if [ -f servers/cpp-mcp/CMakeLists.txt ]; then bash servers/cpp-mcp/build.sh || true; fi
YML

  write_file "$WORKSPACE_ROOT/.github/workflows/docs.yml" 0644 <<'YML'
name: Update Docs

on:
  workflow_dispatch:
  push:
    paths: [ 'docs/**' ]

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Upload docs artifact
        uses: actions/upload-artifact@v4
        with:
          name: site-docs
          path: docs/
YML

  write_file "$WORKSPACE_ROOT/.github/workflows/code-review.yml" 0644 <<'YML'
name: Code Review

on:
  pull_request:
    branches: [ main ]

jobs:
  pr_checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint Python
        run: |
          python -m pip install ruff || true
          ruff check . || true
      - name: Type-check (mypy)
        run: |
          python -m pip install mypy || true
          mypy . || true
YML
}

scaffold_devcontainer_and_containerfiles() {
  if [ "$(json_get '.enable.devcontainer')" != "true" ]; then return 0; fi
  log "Scaffolding devcontainer, Containerfile, Docker deployment"

  # Containerfile (Podman)
  write_file "$WORKSPACE_ROOT/Containerfile" 0644 <<'DOCKER'
FROM alpine:3.20
RUN apk add --no-cache ca-certificates bash && update-ca-certificates
WORKDIR /app
COPY . /app
CMD ["/bin/sh"]
DOCKER

  # Devcontainer config
  write_file "$WORKSPACE_ROOT/devcontainer/devcontainer.json" 0644 <<'JSON'
{
  "name": "Cursor Orchestrator Dev",
  "image": "mcr.microsoft.com/devcontainers/base:debian",
  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "lts"
    },
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    }
  },
  "postCreateCommand": "bash scripts/post-create.sh"
}
JSON

  write_file "$WORKSPACE_ROOT/scripts/post-create.sh" 0755 <<'SH'
#!/usr/bin/env bash
set -euo pipefail
echo "Devcontainer post-create hook"
SH

  # Docker deployment example
  local agent_port
  agent_port="$(json_get '.backgroundAgent.port')"
  if [ -z "$agent_port" ] || [ "$agent_port" = "null" ]; then agent_port="8088"; fi
  write_file "$WORKSPACE_ROOT/Dockerfile" 0644 <<DOCKER
FROM python:3.11-slim
WORKDIR /app
COPY services/background-agent/requirements.txt /app/requirements.txt
RUN pip install -U pip && pip install -r /app/requirements.txt
COPY services/background-agent /app/services/background-agent
EXPOSE ${agent_port}
CMD ["uvicorn", "services.background-agent.main:app", "--host", "0.0.0.0", "--port", "${agent_port}"]
DOCKER

  write_file "$WORKSPACE_ROOT/compose.yaml" 0644 <<YAML
services:
  background-agent:
    build: .
    ports:
      - "${agent_port}:${agent_port}"
    restart: unless-stopped
YAML
}

scaffold_aws_terraform() {
  if [ "$(json_get '.enable.awsTerraform')" != "true" ]; then return 0; fi
  log "Scaffolding AWS Terraform template"
  write_file "$WORKSPACE_ROOT/infra/aws/terraform/main.tf" 0644 <<'TF'
terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}
TF

  write_file "$WORKSPACE_ROOT/infra/aws/terraform/.gitignore" 0644 <<'IGN'
.terraform/
terraform.tfstate*
IGN
}

scaffold_web_and_mcp_json() {
  if [ "$(json_get '.enable.webAndMcp')" != "true" ]; then return 0; fi
  log "Scaffolding web project and browser tools mcp.json"
  write_file "$WORKSPACE_ROOT/web/README.md" 0644 <<'MD'
# Web Dev + Testing

Use this directory for web development. Add e2e tests and tools.
MD

  write_file "$WORKSPACE_ROOT/web/mcp.json" 0644 <<'JSON'
{
  "tools": [
    "large-codebases",
    "mermaid-diagrams"
  ]
}
JSON
}

scaffold_cpp_conan_and_esp32() {
  if [ "$(json_get '.enable.cppConan')" != "true" ] && [ "$(json_get '.enable.esp32')" != "true" ]; then return 0; fi
  log "Scaffolding C++ with Conan and ESP32 container template"
  # C++ + Conan
  mkdir -p "$WORKSPACE_ROOT/cpp-conan/src"
  write_file "$WORKSPACE_ROOT/cpp-conan/conanfile.txt" 0644 <<'TXT'
[requires]

[generators]
CMakeDeps
CMakeToolchain
TXT

  write_file "$WORKSPACE_ROOT/cpp-conan/CMakeLists.txt" 0644 <<'CMAKE'
cmake_minimum_required(VERSION 3.16)
project(cpp_conan_example LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_executable(app src/main.cpp)
CMAKE

  write_file "$WORKSPACE_ROOT/cpp-conan/src/main.cpp" 0644 <<'CPP'
#include <iostream>
int main() { std::cout << "Hello from Conan template" << std::endl; }
CPP

  # ESP32 containerized builder (placeholder)
  if [ "$(json_get '.enable.esp32')" = "true" ]; then
    write_file "$WORKSPACE_ROOT/esp32/Dockerfile" 0644 <<'DOCKER'
FROM espressif/idf:latest
WORKDIR /workspace
CMD ["/bin/bash"]
DOCKER

    write_file "$WORKSPACE_ROOT/esp32/README.md" 0644 <<'MD'
# ESP32 Containerized Builder

Use the `espressif/idf` image to build ESP32 targets without local SDK installs.
MD
  fi
}

scaffold_android_kotlin_container() {
  if [ "$(json_get '.enable.android')" != "true" ]; then return 0; fi
  log "Scaffolding Android Kotlin containerized builder (minimal)"
  write_file "$WORKSPACE_ROOT/android/Dockerfile" 0644 <<'DOCKER'
FROM eclipse-temurin:17-jdk
ENV ANDROID_SDK_ROOT=/opt/android-sdk
RUN mkdir -p "$ANDROID_SDK_ROOT" /opt/tools \
    && apt-get update && apt-get install -y --no-install-recommends unzip wget ca-certificates && rm -rf /var/lib/apt/lists/* \
    && wget -q https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip -O /opt/tools/cmdline-tools.zip \
    && unzip -q /opt/tools/cmdline-tools.zip -d /opt/tools \
    && mkdir -p $ANDROID_SDK_ROOT/cmdline-tools/latest \
    && mv /opt/tools/cmdline-tools $ANDROID_SDK_ROOT/cmdline-tools/latest \
    && yes | $ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager --licenses || true
DOCKER

  write_file "$WORKSPACE_ROOT/android/README.md" 0644 <<'MD'
# Android Native Kotlin (Containerized Builder)

Container image with JDK and Android SDK command-line tools.
MD
}

scaffold_readme() {
  log "Writing project README with usage instructions"
  write_file "$WORKSPACE_ROOT/README.md" 0644 <<'MD'
# Cursor Orchestration Environment

This repository was initialized by `scripts/setup_orchestrator.sh`.

Key components:
- `.cursor/` MCP config, tools, rules, hooks, webhooks, agents
- `servers/` MCP server templates for Python, TypeScript, C++
- `services/background-agent` FastAPI webhook receiver
- `.github/workflows/` CI workflows
- `devcontainer/`, `Containerfile`, `Dockerfile`, `compose.yaml`
- `infra/aws/terraform` starter
- `cpp-conan`, `esp32`, `android` templates

Getting started:
```bash
# Run background agent
bash scripts/run-background-agent.sh

# Build TS server
npm --prefix servers/ts-mcp run build

# Build C++ server
bash servers/cpp-mcp/build.sh
```
MD
}

attempt_install_cursor_cli() {
  log "Attempting to install Cursor-related CLIs (best-effort)"
  if have_cmd npm; then
    # These package names are placeholders; if they don't exist, the step is skipped gracefully.
    npm install -g @cursor/cli 2>/dev/null || true
    npm install -g cursor-agent 2>/dev/null || true
    npm install -g @cursor/agent 2>/dev/null || true
  else
    warn "npm not available; skipping Cursor CLI attempts"
  fi
}

main() {
  log "Starting $SCRIPT_NAME at $START_TS"
  WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
  if [ ! -d "$WORKSPACE_ROOT" ]; then WORKSPACE_ROOT="$(pwd)"; fi
  export WORKSPACE_ROOT
  CONFIG_PATH="${CONFIG_PATH:-$WORKSPACE_ROOT/config/project_orchestration.json}"
  if ! have_cmd jq; then
    require_or_install_pkg jq jq || die "jq is required to parse JSON config"
  fi
  if [ ! -f "$CONFIG_PATH" ]; then
    warn "Config not found at $CONFIG_PATH; creating defaults"
    mkdir -p "$(dirname "$CONFIG_PATH")"
    cat >"$CONFIG_PATH" <<'JSON'
{
  "enable": {"cursorConfigs": true, "pythonMcp": true, "tsMcp": true, "cppMcp": true, "mcpClient": true, "backgroundAgent": true, "githubActions": true, "devcontainer": true, "awsTerraform": true, "webAndMcp": true, "cppConan": true, "esp32": true, "android": true},
  "ports": {"pyMcpPort": 8765, "tsMcpPort": 8766},
  "backgroundAgent": {"host": "127.0.0.1", "port": 8088},
  "tools": {"largeCodebases": {"enabled": true, "exclude": ["node_modules", "build", "dist", ".git", ".venv", "venv"], "maxFileSizeMB": 5}, "mermaid": {"enabled": true}},
  "container": {"prefer": "podman"},
  "runtime": {"node": "lts/*", "python": "3.11"}
}
JSON
  fi
  create_dirs
  install_base_packages
  install_node_via_nvm
  install_python_tools

  setup_cursor_configs
  scaffold_python_mcp_server
  scaffold_ts_mcp_server
  scaffold_cpp_mcp_server
  scaffold_mcp_client_ts
  scaffold_background_agent
  scaffold_github_actions
  scaffold_devcontainer_and_containerfiles
  scaffold_aws_terraform
  scaffold_web_and_mcp_json
  scaffold_cpp_conan_and_esp32
  scaffold_android_kotlin_container
  scaffold_readme
  attempt_install_cursor_cli

  log "Setup complete. Next steps:"
  cat <<'STEPS'
  - Review .cursor configs in .cursor/
  - Start background agent: bash scripts/run-background-agent.sh
  - Build TS server: npm --prefix servers/ts-mcp run build && node servers/ts-mcp/dist/index.js
  - Build C++ server: bash servers/cpp-mcp/build.sh && ./servers/cpp-mcp/build/mcp_server
  - Optionally run container: docker compose up --build
STEPS
}

main "$@"

