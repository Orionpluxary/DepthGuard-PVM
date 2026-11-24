# =============================================================================
# FILE PURPOSE:
# Demonstrates telemetry metrics inspection and reset capabilities in DepthGuard-PVM.
# Shows how to query current call depth, peak depth reached, and warning counts
# at any stage of execution for APM and system profiling.
# Run via: `depthguard-python examples/03_stats_and_telemetry.py`.
# =============================================================================

"""
===============================================================================
DUAL-RUNTIME EXECUTION GUIDE: 03_STATS_AND_TELEMETRY
===============================================================================

🔴 1. RUNNING WITH REGULAR / UNMODIFIED PYTHON:
   Command:
       python examples/03_stats_and_telemetry.py
   Expected Output & Failure Explanation:
       Standard Python lacks call-depth telemetry in the C evaluator:
           AttributeError: module 'sys' has no attribute 'get_depth_stats'
       There is no low-overhead way to inspect recursion depth without expensive
       frame stack inspection (e.g. `len(inspect.stack())` which causes massive slowdown).

🟢 2. RUNNING WITH DEPTHGUARD-PVM RUNTIME:
   Command:
       depthguard-python examples/03_stats_and_telemetry.py
   Expected Output & Success Explanation:
       [DepthGuard-PVM] Initial Stats: {'current_depth': 1, 'max_depth_reached': 1, ...}
       [DepthGuard-PVM] Peaked at recursion depth 42
       [DepthGuard-PVM] Stats after reset: {'current_depth': 1, 'max_depth_reached': 1, ...}
===============================================================================
"""

import sys

def run_demo():
    print("=== DepthGuard-PVM: Stats & Telemetry Demonstration ===")

    if not hasattr(sys, "get_depth_stats"):
        print("\n🔴 [ERROR] Unmodified Python Detected!")
        print("AttributeError: module 'sys' has no attribute 'get_depth_stats'")
        print("Standard Python does not support native PVM call-depth telemetry.")
        print("Please run this script using: depthguard-python examples/03_stats_and_telemetry.py\n")
        sys.exit(1)

    print("\n🟢 [DepthGuard-PVM] Resetting telemetry...")
    sys.reset_depth_stats()
    sys.set_depth_warn(0)
    sys.set_depth_guard(100)

    initial_stats = sys.get_depth_stats()
    print(f"  [1] Initial telemetry: {initial_stats}")

    def bounded_recurse(depth, target):
        if depth >= target:
            # Inspect stats at peak depth
            stats_at_peak = sys.get_depth_stats()
            print(f"  [2] Telemetry at peak recursion (target={target}):")
            for k, v in stats_at_peak.items():
                print(f"        {k}: {v}")
            return depth
        return bounded_recurse(depth + 1, target)

    TARGET = 42
    print(f"\n[DepthGuard-PVM] Executing bounded recursion to target={TARGET}...")
    bounded_recurse(1, TARGET)

    stats_after = sys.get_depth_stats()
    print(f"\n  [3] Telemetry after unwinding:")
    for k, v in stats_after.items():
        print(f"        {k}: {v}")

    print(f"\n  [4] Resetting telemetry stats...")
    sys.reset_depth_stats()
    print(f"  [5] Stats after reset: {sys.get_depth_stats()}")

    sys.set_depth_guard(0)
    print("\nDemo completed successfully.")

if __name__ == "__main__":
    run_demo()
