#!/usr/bin/env bash
# Recreates the local stand-in from scratch: pg1 primary, pg2 streaming standby.
set -euo pipefail
D=${DOCKER:-$HOME/bin/docker}
cd "$(dirname "$0")/../deploy"
$D compose down -v --remove-orphans >/dev/null 2>&1 || true
$D compose up -d --build --wait >/dev/null 2>&1
