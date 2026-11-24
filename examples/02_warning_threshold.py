# =============================================================================
# FILE PURPOSE:
# Demonstrates proactive non-blocking call-depth warnings with sys.set_depth_warn.
# Emits early warning diagnostic alerts to stderr before catastrophic failure,
# allowing telemetry and monitoring systems to track deep call stacks.
# Run via: `depthguard-python examples/02_warning_threshold.py`.
# =============================================================================

"""
===============================================================================
DUAL-RUNTIME EXECUTION GUIDE: 02_WARNING_THRESHOLD
===============================================================================

🔴 1. RUNNING WITH REGULAR / UNMODIFIED PYTHON:
   Command:
       python examples/02_warning_threshold.py
   Expected Output & Failure Explanation:
       Standard Python lacks any non-blocking warning threshold for recursion depth:
           AttributeError: module 'sys' has no attribute 'set_depth_warn'
       Standard Python offers only a binary state: silent execution until sudden fatal crash.

🟢 2. RUNNING WITH DEPTHGUARD-PVM RUNTIME:
   Command:
       depthguard-python examples/02_warning_threshold.py
   Expected Output & Success Explanation:
       [DepthGuard-PVM WARNING] call depth 15 reached
       [SUCCESS] Caught DepthGuard RuntimeError: DepthGuard-PVM: call-depth guard exceeded
       [TELEMETRY] Warnings emitted: 1 | Max depth reached: 31
===============================================================================
"""

import sys
import time

def run_demo():
    print("=== DepthGuard-PVM: Warning Threshold Demonstration ===")

    if not hasattr(sys, "set_depth_warn"):
        print("\n🔴 [ERROR] Unmodified Python Detected!")
        print("AttributeError: module 'sys' has no attribute 'set_depth_warn'")
        print("Standard Python has no warning threshold for recursion depth.")
        print("Please run this script using: depthguard-python examples/02_warning_threshold.py\n")
        sys.exit(1)

    WARN_THRESHOLD = 15
    GUARD_LIMIT = 30

    print(f"\n🟢 [DepthGuard-PVM] Setting warning threshold = {WARN_THRESHOLD}, hard guard = {GUARD_LIMIT}...")
    sys.set_depth_warn(WARN_THRESHOLD)
    sys.set_depth_guard(GUARD_LIMIT)

    def deep_worker(n):
        return deep_worker(n + 1)

    print("[DepthGuard-PVM] Executing deep recursion (watch stderr for warning)...")
    try:
        deep_worker(1)
    except RuntimeError as err:
        print(f"\n[SUCCESS] Caught DepthGuard RuntimeError: {err}")
        stats = sys.get_depth_stats()
        print(f"[TELEMETRY] Warnings emitted: {stats['warnings_emitted']}")
        print(f"[TELEMETRY] Max depth reached: {stats['max_depth_reached']}")

    # Clean up
    sys.set_depth_warn(0)
    sys.set_depth_guard(0)
    print("\nDemo completed successfully.")

if __name__ == "__main__":
    run_demo()
