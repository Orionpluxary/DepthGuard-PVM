# =============================================================================
# FILE PURPOSE:
# High-level Python interface and utilities for DepthGuard-PVM recursion monitoring.
# Provides Pythonic context managers, decorators, typed stats containers, and
# wrappers around CPython's native sys.set_depth_warn and sys.set_depth_guard.
# Can be imported in user projects or executed directly for self-testing.
# =============================================================================

import functools
import sys
import warnings
from typing import Any, Callable, Dict, Optional


def has_native_depthguard() -> bool:
    """Return True if running on a DepthGuard-patched CPython runtime."""
    return hasattr(sys, "set_depth_guard") and hasattr(sys, "get_depth_stats")


class DepthGuardStats:
    """Encapsulates telemetry statistics returned by the DepthGuard runtime."""

    def __init__(self, raw_stats: Dict[str, int]) -> None:
        self.current_depth: int = raw_stats.get("current_depth", 0)
        self.max_depth_reached: int = raw_stats.get("max_depth_reached", 0)
        self.warnings_emitted: int = raw_stats.get("warnings_emitted", 0)
        self.warn_depth: int = raw_stats.get("warn_depth", 0)
        self.max_depth: int = raw_stats.get("max_depth", 0)

    def as_dict(self) -> Dict[str, int]:
        return {
            "current_depth": self.current_depth,
            "max_depth_reached": self.max_depth_reached,
            "warnings_emitted": self.warnings_emitted,
            "warn_depth": self.warn_depth,
            "max_depth": self.max_depth,
        }

    def __repr__(self) -> str:
        return (
            f"DepthGuardStats(current={self.current_depth}, "
            f"max_reached={self.max_depth_reached}, "
            f"warnings={self.warnings_emitted}, "
            f"warn_threshold={self.warn_depth}, "
            f"guard_limit={self.max_depth})"
        )


def set_depth_warn(depth: int) -> None:
    """Set the call-depth warning threshold (0 to disable)."""
    if has_native_depthguard():
        sys.set_depth_warn(depth)  # type: ignore[attr-defined]
    else:
        warnings.warn(
            "Native DepthGuard-PVM is not active in this Python runtime. "
            "set_depth_warn() is a no-op.",
            RuntimeWarning,
            stacklevel=2,
        )


def get_depth_warn() -> int:
    """Retrieve the current warning depth threshold."""
    if has_native_depthguard():
        return sys.get_depth_warn()  # type: ignore[attr-defined]
    return 0


def set_depth_guard(depth: int) -> None:
    """Set the hard recursion call-depth guard limit (0 to disable)."""
    if has_native_depthguard():
        sys.set_depth_guard(depth)  # type: ignore[attr-defined]
    else:
        warnings.warn(
            "Native DepthGuard-PVM is not active in this Python runtime. "
            "set_depth_guard() is a no-op.",
            RuntimeWarning,
            stacklevel=2,
        )


def get_depth_guard() -> int:
    """Retrieve the current hard call-depth guard limit."""
    if has_native_depthguard():
        return sys.get_depth_guard()  # type: ignore[attr-defined]
    return 0


def get_depth_stats() -> DepthGuardStats:
    """Retrieve current recursion call-depth statistics dictionary."""
    if has_native_depthguard():
        return DepthGuardStats(sys.get_depth_stats())  # type: ignore[attr-defined]
    return DepthGuardStats({
        "current_depth": 0,
        "max_depth_reached": 0,
        "warnings_emitted": 0,
        "warn_depth": 0,
        "max_depth": 0,
    })


def reset_depth_stats() -> None:
    """Reset the maximum depth reached and warning emission counters."""
    if has_native_depthguard():
        sys.reset_depth_stats()  # type: ignore[attr-defined]


class DepthGuard:
    """
    Context manager to enforce recursion call-depth warning and guard limits
    within a scoped code block, restoring prior settings on exit.
    """

    def __init__(self, warn: int = 0, guard: int = 0, reset_on_enter: bool = True) -> None:
        self.warn: int = warn
        self.guard: int = guard
        self.reset_on_enter: bool = reset_on_enter
        self._prev_warn: int = 0
        self._prev_guard: int = 0

    def __enter__(self) -> "DepthGuard":
        if has_native_depthguard():
            self._prev_warn = get_depth_warn()
            self._prev_guard = get_depth_guard()
            if self.reset_on_enter:
                reset_depth_stats()
            set_depth_warn(self.warn)
            set_depth_guard(self.guard)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Optional[bool]:
        if has_native_depthguard():
            set_depth_warn(self._prev_warn)
            set_depth_guard(self._prev_guard)
        return None

    @property
    def stats(self) -> DepthGuardStats:
        return get_depth_stats()


def depth_guard(warn: int = 0, max_depth: int = 0) -> Callable:
    """
    Decorator that applies recursion call-depth limits to the decorated function.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with DepthGuard(warn=warn, guard=max_depth):
                return fn(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    print(f"DepthGuard-PVM Module loaded. Native support detected: {has_native_depthguard()}")
    print("Stats:", get_depth_stats())
