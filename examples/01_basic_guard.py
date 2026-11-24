# =============================================================================
# FILE PURPOSE:
# Demonstrates basic recursion call-depth guarding using native sys.set_depth_guard.
# Shows how runaway recursion is intercepted proactively at a user-defined threshold,
# preventing stack overflow and resource exhaustion.
# Run via: `depthguard-python examples/01_basic_guard.py` (or regular python).
# =============================================================================

"""
===============================================================================
DUAL-RUNTIME EXECUTION GUIDE: 01_BASIC_GUARD
===============================================================================

🔴 1. RUNNING WITH REGULAR / UNMODIFIED PYTHON:
   Command:
       python examples/01_basic_guard.py
   Expected Output & Failure Explanation:
       Standard CPython does not possess `sys.set_depth_guard`. The call fails immediately:
           AttributeError: module 'sys' has no attribute 'set_depth_guard'
       Or if bypassed, standard Python runs uncontrollably up to 1,000 frames:
           RecursionError: maximum recursion depth exceeded while calling a Python object
       Standard Python lacks fine-grained, low-overhead depth guarding.

🟢 2. RUNNING WITH DEPTHGUARD-PVM RUNTIME:
   Command:
       depthguard-python examples/01_basic_guard.py
   Expected Output & Success Explanation:
       [DepthGuard-PVM] Configuring hard limit at depth 25...
       [DepthGuard-PVM] Starting runaway recursion...
       [SUCCESS] Caught DepthGuard RuntimeError: DepthGuard-PVM: call-depth guard exceeded
       [TELEMETRY] Intercepted in 12.40 µs | Max depth reached: 26
===============================================================================
"""

import sys
import time

def run_demo():
    print("=== DepthGuard-PVM: Basic Guard Demonstration ===")

    # Check interpreter capability
    if not hasattr(sys, "set_depth_guard"):
        print("\n🔴 [ERROR] Unmodified Python Detected!")
        print("AttributeError: module 'sys' has no attribute 'set_depth_guard'")
        print("Standard Python cannot guard call depth at the PVM level.")
        print("Please run this script using: depthguard-python examples/01_basic_guard.py\n")
        sys.exit(1)

    GUARD_DEPTH = 25
    print(f"\n🟢 [DepthGuard-PVM] Configuring hard limit at depth {GUARD_DEPTH}...")
    sys.set_depth_guard(GUARD_DEPTH)

    call_count = 0
    def runaway_recursion(level):
        nonlocal call_count
        call_count = level
        return runaway_recursion(level + 1)

    t0 = time.perf_counter()
    try:
        print("[DepthGuard-PVM] Starting runaway recursion...")
        runaway_recursion(1)
    except RuntimeError as err:
        elapsed_us = (time.perf_counter() - t0) * 1e6
        print(f"\n[SUCCESS] Caught DepthGuard RuntimeError: {err}")
        print(f"[TELEMETRY] Intercepted in {elapsed_us:.2f} µs | Max depth reached: {call_count + 1}")
        stats = sys.get_depth_stats()
        print(f"[STATS] Telemetry snapshot: {stats}")

    # Clean up guard limit
    sys.set_depth_guard(0)
    print("\nDemo completed successfully.")

if __name__ == "__main__":
    run_demo()
