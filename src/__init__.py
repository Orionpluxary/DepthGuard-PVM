# =============================================================================
# FILE PURPOSE:
# Core package initializer for the DepthGuard-PVM recursion safety framework.
# It exposes high-level Pythonic APIs, context managers, decorators, and native
# CPython sys hooks for recursion call-depth monitoring and runtime guarding.
# Run or import via: `import depthguard` or `from depthguard import DepthGuard`.
# =============================================================================

"""
DepthGuard-PVM: Proactive Recursion Call-Depth Warning & Guard for Python Virtual Machine.
"""

from .depthguard import (
    DepthGuard,
    depth_guard,
    has_native_depthguard,
    set_depth_warn,
    get_depth_warn,
    set_depth_guard,
    get_depth_guard,
    get_depth_stats,
    reset_depth_stats,
    DepthGuardStats,
)

__all__ = [
    "DepthGuard",
    "depth_guard",
    "has_native_depthguard",
    "set_depth_warn",
    "get_depth_warn",
    "set_depth_guard",
    "get_depth_guard",
    "get_depth_stats",
    "reset_depth_stats",
    "DepthGuardStats",
]

__version__ = "1.0.0"
