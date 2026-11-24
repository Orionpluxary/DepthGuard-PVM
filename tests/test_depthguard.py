# =============================================================================
# FILE PURPOSE:
# Comprehensive automated unit and integration test suite for DepthGuard-PVM.
# Validates call-depth warnings, hard guard thresholds, telemetry statistics,
# context managers, and decorator mechanics under extreme recursion.
# Run via: `depthguard-python -m unittest tests/test_depthguard.py` or `pytest tests/`.
# =============================================================================

import sys
import unittest
import io
from contextlib import redirect_stderr
import os

# Ensure src/ is on sys.path for importing depthguard
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from depthguard import (
    DepthGuard,
    depth_guard,
    has_native_depthguard,
    set_depth_warn,
    get_depth_warn,
    set_depth_guard,
    get_depth_guard,
    get_depth_stats,
    reset_depth_stats,
)


class TestDepthGuardNative(unittest.TestCase):
    """Test suite targeting CPython runtime DepthGuard-PVM modifications."""

    def setUp(self):
        """Ensure clean state before every test."""
        if has_native_depthguard():
            reset_depth_stats()
            set_depth_warn(0)
            set_depth_guard(0)

    def tearDown(self):
        """Clean up limits after tests."""
        if has_native_depthguard():
            reset_depth_stats()
            set_depth_warn(0)
            set_depth_guard(0)

    def test_native_hooks_presence(self):
        """Verify native DepthGuard C-level hooks exist on sys."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present in standard Python.")
        self.assertTrue(hasattr(sys, "set_depth_warn"))
        self.assertTrue(hasattr(sys, "get_depth_warn"))
        self.assertTrue(hasattr(sys, "set_depth_guard"))
        self.assertTrue(hasattr(sys, "get_depth_guard"))
        self.assertTrue(hasattr(sys, "get_depth_stats"))
        self.assertTrue(hasattr(sys, "reset_depth_stats"))

    def test_warn_limit_get_set(self):
        """Test getting and setting warning threshold."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present.")
        try:
            set_depth_warn(42)
            self.assertEqual(get_depth_warn(), 42)
            set_depth_warn(0)
            self.assertEqual(get_depth_warn(), 0)

            with self.assertRaises(ValueError):
                sys.set_depth_warn(-5)
        finally:
            set_depth_warn(0)

    def test_guard_limit_get_set(self):
        """Test getting and setting hard guard limit."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present.")
        try:
            set_depth_guard(100)
            self.assertEqual(get_depth_guard(), 100)
            set_depth_guard(0)
            self.assertEqual(get_depth_guard(), 0)

            with self.assertRaises(ValueError):
                sys.set_depth_guard(-10)
        finally:
            set_depth_guard(0)

    def test_guard_interception_runtime_error(self):
        """Test that exceeding the guard depth triggers RuntimeError immediately."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present.")

        try:
            set_depth_guard(20)

            def recurse(n):
                return recurse(n + 1)

            with self.assertRaises(RuntimeError) as ctx:
                recurse(1)

            self.assertIn("DepthGuard-PVM: call-depth guard exceeded", str(ctx.exception))
        finally:
            set_depth_guard(0)

    def test_warn_emission_and_telemetry(self):
        """Verify warning message is output to stderr and counted in stats."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present.")

        try:
            set_depth_warn(12)
            set_depth_guard(30)

            def recurse(level):
                return recurse(level + 1)

            stderr_buffer = io.StringIO()
            with redirect_stderr(stderr_buffer):
                try:
                    recurse(1)
                except RuntimeError:
                    pass

            stats = get_depth_stats()
            self.assertGreaterEqual(stats.warnings_emitted, 1)
            self.assertGreaterEqual(stats.max_depth_reached, 30)
            self.assertIn("[DepthGuard-PVM WARNING] call depth 12 reached", stderr_buffer.getvalue())
        finally:
            set_depth_warn(0)
            set_depth_guard(0)

    def test_stats_reset(self):
        """Verify resetting telemetry stats."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present.")

        try:
            set_depth_guard(15)

            def recurse(n):
                return recurse(n + 1)

            try:
                recurse(1)
            except RuntimeError:
                pass

            stats_before = get_depth_stats()
            self.assertGreaterEqual(stats_before.max_depth_reached, 15)
        finally:
            set_depth_guard(0)

        reset_depth_stats()
        stats_after = get_depth_stats()
        self.assertEqual(stats_after.warnings_emitted, 0)
        self.assertLessEqual(stats_after.max_depth_reached, stats_after.current_depth + 4)

    def test_context_manager_scoping(self):
        """Test DepthGuard context manager scoping and restoring prior limits."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present.")

        set_depth_warn(5)
        set_depth_guard(50)

        with DepthGuard(warn=10, guard=25):
            self.assertEqual(get_depth_warn(), 10)
            self.assertEqual(get_depth_guard(), 25)

            def recurse(n):
                return recurse(n + 1)

            with self.assertRaises(RuntimeError):
                recurse(1)

        # Restored outer limits
        self.assertEqual(get_depth_warn(), 5)
        self.assertEqual(get_depth_guard(), 50)

    def test_decorator_scoping(self):
        """Test @depth_guard decorator applies and restores limits."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present.")

        @depth_guard(warn=0, max_depth=16)
        def limited_worker(n):
            return limited_worker(n + 1)

        with self.assertRaises(RuntimeError):
            limited_worker(1)

        # Limits should be restored to zero
        self.assertEqual(get_depth_guard(), 0)

    def test_safe_execution_below_guard(self):
        """Test that recursive functions staying below guard limit succeed without penalty."""
        if not has_native_depthguard():
            self.skipTest("Native DepthGuard-PVM not present.")

        try:
            set_depth_guard(50)

            def safe_recurse(n):
                if n <= 1:
                    return 1
                return n * safe_recurse(n - 1)

            result = safe_recurse(10)
            self.assertEqual(result, 3628800)
        finally:
            set_depth_guard(0)


if __name__ == "__main__":
    unittest.main()
