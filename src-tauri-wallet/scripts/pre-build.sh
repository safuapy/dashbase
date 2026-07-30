#!/usr/bin/env bash
# Pre-build script: copies daemon binary into Tauri resources if available
# This runs before tauri build to bundle the daemon inside the app

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESOURCES_DIR="$SCRIPT_DIR/../src-tauri/resources"

mkdir -p "$RESOURCES_DIR"

# Check if daemon binary exists in resources already (placed by CI)
if [ -f "$RESOURCES_DIR/dashbased" ] || [ -f "$RESOURCES_DIR/dashbased.exe" ]; then
  echo "[pre-build] Daemon binary already in resources/"
  exit 0
fi

# Check common locations for daemon binary
DAEMON_PATHS=(
  "$SCRIPT_DIR/../../src/dashbased"
  "$SCRIPT_DIR/../../release/opt/dashbase/bin/dashbased"
  "$(which dashbased 2>/dev/null || true)"
)

for path in "${DAEMON_PATHS[@]}"; do
  if [ -n "$path" ] && [ -f "$path" ]; then
    echo "[pre-build] Found daemon at: $path"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
      cp "$path" "$RESOURCES_DIR/dashbased.exe"
    else
      cp "$path" "$RESOURCES_DIR/dashbased"
      chmod +x "$RESOURCES_DIR/dashbased"
    fi
    echo "[pre-build] Daemon binary copied to resources/"
    exit 0
  fi
done

echo "[pre-build] No daemon binary found. Wallet will work with external daemon only."
exit 0
