#!/bin/bash
# SessionStart hook for Claude Code on the web.
#
# Detects the project's dependency manifests and installs them so tests,
# linters, and the Claude API SDK are ready when the agent loop starts.
# Stack-agnostic on purpose — this repo is a template. It does nothing
# until real project code is added.
#
# Runs synchronously (no async line) so the agent can trust that
# dependencies are ready. Flip to async later if startup latency hurts.

set -euo pipefail

# Only do heavy work on remote (web) sessions. Local sessions keep their
# own env and shouldn't be blocked by dep installs.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$PWD}"

log() { echo "[session-start] $*" >&2; }

# --- Node / TypeScript -------------------------------------------------------
if [ -f package.json ]; then
  if [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1; then
    log "pnpm install"
    pnpm install --prefer-offline
  elif [ -f yarn.lock ] && command -v yarn >/dev/null 2>&1; then
    log "yarn install"
    yarn install --prefer-offline
  elif command -v npm >/dev/null 2>&1; then
    log "npm install"
    npm install --prefer-offline --no-audit --no-fund
  else
    log "package.json found but no Node package manager available"
  fi
fi

# --- Python ------------------------------------------------------------------
if [ -f pyproject.toml ]; then
  if [ -f uv.lock ] && command -v uv >/dev/null 2>&1; then
    log "uv sync"
    uv sync
    echo "export PATH=\"$PWD/.venv/bin:\$PATH\"" >> "${CLAUDE_ENV_FILE:-/dev/null}" 2>/dev/null || true
  elif [ -f poetry.lock ] && command -v poetry >/dev/null 2>&1; then
    log "poetry install"
    poetry install --no-interaction
  elif command -v pip >/dev/null 2>&1; then
    log "pip install -e ."
    pip install --quiet -e .
  fi
elif [ -f requirements.txt ] && command -v pip >/dev/null 2>&1; then
  log "pip install -r requirements.txt"
  pip install --quiet -r requirements.txt
fi

# --- Rust --------------------------------------------------------------------
if [ -f Cargo.toml ] && command -v cargo >/dev/null 2>&1; then
  log "cargo fetch"
  cargo fetch
fi

# --- Go ----------------------------------------------------------------------
if [ -f go.mod ] && command -v go >/dev/null 2>&1; then
  log "go mod download"
  go mod download
fi

# --- Ruby --------------------------------------------------------------------
if [ -f Gemfile ] && command -v bundle >/dev/null 2>&1; then
  log "bundle install"
  bundle install --quiet
fi

log "done"
