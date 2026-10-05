#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "run this installer with sudo"
  exit 1
fi

PYTHON=${PYTHON:-python3}

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "python3 is required to install Pack"
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

"$PYTHON" -m pip install --break-system-packages "$REPO_DIR" 2>/dev/null || \
"$PYTHON" -m pip install "$REPO_DIR"

echo
echo "Pack installed. Starting first-time setup…"
pack setup
