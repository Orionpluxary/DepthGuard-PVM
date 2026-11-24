# =============================================================================
# FILE PURPOSE:
# System installation script for DepthGuard-PVM self-contained SDK archive.
# Extracts depthguard-pvm-sdk.tar.gz into /opt and symlinks the binary to
# /usr/local/bin/depthguard-python for direct system-wide accessibility.
# Run via: `sudo bash scripts/install.sh [optional_tar_path]`.
# =============================================================================

#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAR_FILE="${1:-${SCRIPT_DIR}/../depthguard-pvm-sdk.tar.gz}"

if [ ! -f "$TAR_FILE" ]; then
    # Fallback to current working directory or home directory
    if [ -f "${SCRIPT_DIR}/depthguard-pvm-sdk.tar.gz" ]; then
        TAR_FILE="${SCRIPT_DIR}/depthguard-pvm-sdk.tar.gz"
    elif [ -f "$HOME/pvm-depthguard/depthguard-pvm-sdk.tar.gz" ]; then
        TAR_FILE="$HOME/pvm-depthguard/depthguard-pvm-sdk.tar.gz"
    else
        echo "Error: Archive depthguard-pvm-sdk.tar.gz not found!" >&2
        echo "Searched locations: ${TAR_FILE}, ${SCRIPT_DIR}, $HOME/pvm-depthguard" >&2
        exit 1
    fi
fi

echo "[DepthGuard-PVM Installer] Extracting $TAR_FILE to /opt..."
sudo mkdir -p /opt
sudo tar -xzf "$TAR_FILE" -C /opt

TARGET_BIN=$(ls -1 /opt/depthguard-pvm/bin/python3.* 2>/dev/null | grep -E "python3\.[0-9]+$" | head -n 1)
if [ -z "$TARGET_BIN" ] || [ ! -x "$TARGET_BIN" ]; then
    TARGET_BIN="/opt/depthguard-pvm/bin/python3"
fi

echo "[DepthGuard-PVM Installer] Creating symlink /usr/local/bin/depthguard-python -> $TARGET_BIN"
sudo mkdir -p /usr/local/bin
sudo ln -sf "$TARGET_BIN" /usr/local/bin/depthguard-python

echo "[DepthGuard-PVM Installer] Successfully installed DepthGuard-PVM!"
echo -n "Installed Python version: "
/usr/local/bin/depthguard-python --version
