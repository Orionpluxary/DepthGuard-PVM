# =============================================================================
# FILE PURPOSE:
# Automated build, compilation, and SDK packaging script for DepthGuard-PVM.
# Compiles patched CPython with make, installs into /opt/depthguard-pvm, and
# packages the complete self-contained runtime into depthguard-pvm-sdk.tar.gz.
# Run via: `bash scripts/build_and_package.sh`.
# =============================================================================

#!/bin/bash
set -euo pipefail

CPYTHON_SRC="${1:-$HOME/pvm-depthguard/cpython-src}"
SDK_OUTPUT_DIR="${2:-$HOME/pvm-depthguard}"

echo "=== [DepthGuard-PVM] Compiling CPython in ${CPYTHON_SRC} ==="
cd "$CPYTHON_SRC"
make -j"$(nproc)"

echo "=== [DepthGuard-PVM] Installing into /opt/depthguard-pvm ==="
sudo make altinstall

echo "=== [DepthGuard-PVM] Verifying installed python binary ==="
INSTALLED_PY=$(ls -1 /opt/depthguard-pvm/bin/python3.* | grep -E "python3\.[0-9]+$" | head -n 1)
echo "Installed binary: $INSTALLED_PY"
"$INSTALLED_PY" --version

echo "=== [DepthGuard-PVM] Ensuring /opt/depthguard-pvm/bin/python3 symlink ==="
if [ ! -f /opt/depthguard-pvm/bin/python3 ]; then
    sudo ln -sf "$INSTALLED_PY" /opt/depthguard-pvm/bin/python3
fi

echo "=== [DepthGuard-PVM] Packaging SDK into ${SDK_OUTPUT_DIR}/depthguard-pvm-sdk.tar.gz ==="
cd "$SDK_OUTPUT_DIR"
sudo tar -czf depthguard-pvm-sdk.tar.gz -C /opt depthguard-pvm
sudo chown "$(id -u):$(id -g)" depthguard-pvm-sdk.tar.gz
ls -lh depthguard-pvm-sdk.tar.gz

echo "=== [DepthGuard-PVM] Packaging complete ==="
