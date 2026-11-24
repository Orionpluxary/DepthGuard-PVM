# =============================================================================
# FILE PURPOSE:
# Demonstrates Pythonic context manager and decorator wrappers for DepthGuard-PVM.
# Illustrates elegant, scoped recursion guards for individual critical code blocks
# or functions without manually touching global sys state.
# Run via: `depthguard-python examples/04_decorator_and_context.py`.
# =============================================================================

"""
===============================================================================
DUAL-RUNTIME EXECUTION GUIDE: 04_DECORATOR_AND_CONTEXT
===============================================================================

🔴 1. RUNNING WITH REGULAR / UNMODIFIED PYTHON:
   Command:
       python examples/04_decorator_and_context.py
   Expected Output & Failure Explanation:
       Standard Python emits a RuntimeWarning:
           RuntimeWarning: Native DepthGuard-PVM is not active in this Python runtime.
       Execution falls back to standard recursion behavior without C-level acceleration.

🟢 2. RUNNING WITH DEPTHGUARD-PVM RUNTIME:
   Command:
       depthguard-python examples/04_decorator_and_context.py
   Expected Output & Success Explanation:
       [DepthGuard-PVM] Context Manager protected block safely caught RuntimeError!
       [DepthGuard-PVM] Decorated function protected block safely caught RuntimeError!
       [DepthGuard-PVM] Outer limits preserved and restored automatically.
===============================================================================
"""

import os
import sys

# Add src/ to path for depthguard import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from depthguard import (
    DepthGuard,
    depth_guard,
    get_depth_guard,
    get_depth_warn,
    has_native_depthguard,
)

def run_demo():
    print("=== DepthGuard-PVM: Context Manager & Decorator Demonstration ===")

    native = has_native_depthguard()
    print(f"Native DepthGuard Support: {'[ACTIVE]' if native else '[FALLBACK MODE]'}")

    # 1. Scoped Context Manager
    print("\n[1] Testing Scoped Context Manager (warn=10, guard=20)...")
    with DepthGuard(warn=10, guard=20) as guard_scope:
        print(f"    Inside context: warn={get_depth_warn()}, guard={get_depth_guard()}")

        def recurse_context(level):
            return recurse_context(level + 1)

        try:
            recurse_context(1)
        except RuntimeError as err:
            print(f"    Caught expected RuntimeError inside context: {err}")
            print(f"    Stats inside context: {guard_scope.stats}")

    print(f"    Exited context. Restored outer guard: {get_depth_guard()}")

    # 2. Scoped Decorator
    print("\n[2] Testing Function Decorator @depth_guard(warn=5, max_depth=15)...")

    @depth_guard(warn=5, max_depth=15)
    def parse_nested_ast(depth):
        return parse_nested_ast(depth + 1)

    try:
        parse_nested_ast(1)
    except RuntimeError as err:
        print(f"    Caught expected RuntimeError in decorated function: {err}")

    print(f"    Exited decorated call. Restored outer guard: {get_depth_guard()}")
    print("\nDemo completed successfully.")

if __name__ == "__main__":
    run_demo()
