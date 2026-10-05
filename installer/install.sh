#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "python3 is required before installing Pack"
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

# Pack is a user program. System package managers ask for sudo only when needed.
"$PYTHON" -m pip install --user --break-system-packages --upgrade --force-reinstall "$REPO_DIR"

USER_BIN="$HOME/.local/bin"
if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
  export PATH="$USER_BIN:$PATH"
  echo "note: add $USER_BIN to PATH if 'pack' is not found in a new terminal"
fi

echo
echo "Pack installed 📦"
echo "Pack setup will ask for sudo only when a selected manager needs system access."
pack setup
