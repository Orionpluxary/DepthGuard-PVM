# =============================================================================
# FILE PURPOSE:
# Main entrypoint and comprehensive architectural codebase map for DepthGuard-PVM.
# Contains a structural breakdown of the entire repository and executes a
# self-contained quick-start demo validating runtime recursion call-depth guards.
# Run via: `depthguard-python src/main.py` or `python src/main.py`.
# =============================================================================

"""
===============================================================================
DEPTHGUARD-PVM REPOSITORY & CODEBASE ARCHITECTURE MAP
===============================================================================

.
├── .gitignore                          # Standard git ignore definitions (build, venv, caches)
├── COMPARISON.md                       # Comprehensive before-and-after source code diff & architecture
├── README.md                           # Publication-grade technical documentation, diagrams & guides
│
├── src/                                # Core Python package and runtime interfaces
│   ├── __init__.py                     # Package exports, versioning, and top-level symbols
│   ├── depthguard.py                   # High-level Python wrappers, DepthGuard context manager & decorator
│   └── main.py                         # Central codebase map & runnable quick-start demo
│
├── scripts/                            # Build, patch, compilation, and installer scripts
│   ├── patch_depthguard.py             # CPython source patcher with preserved upstream code comments
│   ├── build_and_package.sh            # Automated CPython compilation and SDK tarball packager
│   └── install.sh                      # System-wide SDK installer into /opt and /usr/local/bin
│
├── tests/                              # Automated test suite
│   └── test_depthguard.py              # Pytest/unittest suite validating warning, guard, and telemetry
│
└── examples/                           # Runnable dual-runtime comparison demonstrations
    ├── 01_basic_guard.py               # Basic recursion limit enforcement triggering RuntimeError
    ├── 02_warning_threshold.py         # Non-blocking warning threshold logging to stderr
    ├── 03_stats_and_telemetry.py       # Live telemetry querying and statistics reset verification
    └── 04_decorator_and_context.py     # Pythonic context manager and function decorator usage
===============================================================================
"""

import sys
import time

try:
    from depthguard import (
        DepthGuard,
        depth_guard,
        get_depth_guard,
        get_depth_stats,
        get_depth_warn,
        has_native_depthguard,
        reset_depth_stats,
        set_depth_guard,
        set_depth_warn,
    )
except ImportError:
    # Allow running directly inside src/
    from .depthguard import (
        DepthGuard,
        depth_guard,
        get_depth_guard,
        get_depth_stats,
        get_depth_warn,
        has_native_depthguard,
        reset_depth_stats,
        set_depth_guard,
        set_depth_warn,
    )


def run_quickstart():
    print("=" * 70)
    print("   DepthGuard-PVM: Proactive Call-Depth Warning & Guard Quickstart")
    print("=" * 70)

    native_active = has_native_depthguard()
    print(f"Python Runtime: {sys.version.split()[0]}")
    print(f"Native DepthGuard Active: {'[YES]' if native_active else '[NO - Fallback Mode]'}")

    if not native_active:
        print("\n[INFO] This interpreter does not have native C-level DepthGuard-PVM hooks.")
        print("To experience native sub-microsecond call-depth enforcement, execute with:")
        print("    /usr/local/bin/depthguard-python src/main.py\n")
        return

    # 1. Inspect initial telemetry
    initial_stats = get_depth_stats()
    print(f"\n[1] Initial Telemetry: {initial_stats}")

    # 2. Configure thresholds
    WARN_LIMIT = 15
    GUARD_LIMIT = 30
    set_depth_warn(WARN_LIMIT)
    set_depth_guard(GUARD_LIMIT)
    print(f"[2] Configured limits: Warning at depth {get_depth_warn()}, Guard at depth {get_depth_guard()}")

    # 3. Recursive probe
    print(f"\n[3] Triggering recursive function to test thresholds...")
    depth_counter = 0

    def recursive_function(level):
        nonlocal depth_counter
        depth_counter = level
        return recursive_function(level + 1)

    t0 = time.perf_counter()
    caught_expected = False
    try:
        recursive_function(1)
    except RuntimeError as err:
        elapsed = (time.perf_counter() - t0) * 1e6
        caught_expected = True
        print(f"    --> Caught expected RuntimeError: {err}")
        print(f"    --> Intercepted in {elapsed:.2f} microseconds at level {depth_counter}")

    assert caught_expected, "DepthGuard failed to trigger RuntimeError!"

    # 4. Check telemetry stats
    stats = get_depth_stats()
    print(f"\n[4] Post-Recursion Telemetry:")
    for k, v in stats.as_dict().items():
        print(f"    - {k}: {v}")

    # 5. Clean reset
    reset_depth_stats()
    set_depth_warn(0)
    set_depth_guard(0)
    print(f"\n[5] Cleaned up limits and reset stats: {get_depth_stats()}")
    print("\n[SUCCESS] DepthGuard-PVM quickstart completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    run_quickstart()
