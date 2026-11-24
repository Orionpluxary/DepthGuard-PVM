# =============================================================================
# FILE PURPOSE:
# Core CPython source tree patching script for DepthGuard-PVM.
# Modifies pycore_ceval.h, ceval.c, ceval_macros.h, and sysmodule.c to inject
# sub-microsecond recursion call-depth monitoring, warning, and guard hooks.
# Run via: `python scripts/patch_depthguard.py [optional_path_to_cpython_src]`.
# =============================================================================

"""
CPython DepthGuard-PVM Patching Utility
---------------------------------------
Applies call-depth warning, guard, and telemetry hooks to the Python Virtual Machine (PVM).
Preserves exact upstream CPython original code in comments alongside all modifications.
"""

import os
import sys

# Default to ~/pvm-depthguard/cpython-src if no path argument provided
if len(sys.argv) > 1:
    base_dir = os.path.abspath(sys.argv[1])
else:
    base_dir = os.path.expanduser("~/pvm-depthguard/cpython-src")

print(f"[DepthGuard Patcher] Target CPython directory: {base_dir}")
if not os.path.isdir(base_dir):
    print(f"Warning: Directory '{base_dir}' does not exist. Ensure CPython source is checked out.")

# =============================================================================
# 1. Include/internal/pycore_ceval.h
# =============================================================================
# -----------------------------------------------------------------------------
# EXACT ORIGINAL CPYTHON CODE (pycore_ceval.h):
# -----------------------------------------------------------------------------
# static inline void _Py_LeaveRecursiveCall(void)  {
# }
# -----------------------------------------------------------------------------
# MODIFIED CODE WITH DEPTHGUARD HOOKS:
# -----------------------------------------------------------------------------
marker_h = "static inline void _Py_LeaveRecursiveCall(void)  {\n}"
new_h = """static inline void _Py_LeaveRecursiveCall(void)  {
}

/* ========================================================================= */
/* --- DepthGuard-PVM API Declarations ------------------------------------- */
/* ========================================================================= */
PyAPI_FUNC(int) _Py_DepthGuard_Enter(PyThreadState *tstate);
PyAPI_FUNC(void) _Py_DepthGuard_Leave(PyThreadState *tstate);
PyAPI_FUNC(void) _Py_DepthGuard_SetWarn(int depth);
PyAPI_FUNC(int) _Py_DepthGuard_GetWarn(void);
PyAPI_FUNC(void) _Py_DepthGuard_SetGuard(int depth);
PyAPI_FUNC(int) _Py_DepthGuard_GetGuard(void);
PyAPI_FUNC(PyObject *) _Py_DepthGuard_GetStats(void);
PyAPI_FUNC(void) _Py_DepthGuard_ResetStats(void);"""

path_h = os.path.join(base_dir, "Include/internal/pycore_ceval.h")
if os.path.isfile(path_h):
    with open(path_h, "r") as f:
        content_h = f.read()
    if marker_h in content_h:
        content_h = content_h.replace(marker_h, new_h, 1)
        with open(path_h, "w") as f:
            f.write(content_h)
        print("  [+] Successfully patched Include/internal/pycore_ceval.h")
    else:
        print("  [*] pycore_ceval.h: Target marker already patched or not found.")


# =============================================================================
# 2. Python/ceval.c
# =============================================================================
# -----------------------------------------------------------------------------
# EXACT ORIGINAL CPYTHON CODE (ceval.c):
# -----------------------------------------------------------------------------
# int _Py_CheckRecursiveCallPy(
#     PyThreadState *tstate)
# -----------------------------------------------------------------------------
# MODIFIED CODE WITH DEPTHGUARD CORE IMPLEMENTATION:
# -----------------------------------------------------------------------------
marker_ceval = """int _Py_CheckRecursiveCallPy(
    PyThreadState *tstate)"""

depthguard_impl = """/* ========================================================================= */
/* --- DepthGuard-PVM Core State & Implementation -------------------------- */
/* ========================================================================= */

typedef struct {
    int current_depth;
    int max_depth_reached;
    int warnings_emitted;
    int warn_depth;
    int max_depth;
    int in_warning;
} _PyDepthGuardState;

static _PyDepthGuardState _depthguard = {0, 0, 0, 0, 0, 0};

int
_Py_DepthGuard_Enter(PyThreadState *tstate)
{
    _depthguard.current_depth++;
    if (_depthguard.current_depth > _depthguard.max_depth_reached) {
        _depthguard.max_depth_reached = _depthguard.current_depth;
    }

    if (_depthguard.warn_depth > 0 &&
        _depthguard.current_depth == _depthguard.warn_depth &&
        !_depthguard.in_warning)
    {
        _depthguard.in_warning = 1;
        _depthguard.warnings_emitted++;
        PySys_WriteStderr("[DepthGuard-PVM WARNING] call depth %d reached\\n", _depthguard.current_depth);
        _depthguard.in_warning = 0;
    }

    if (_depthguard.max_depth > 0 && _depthguard.current_depth > _depthguard.max_depth) {
        _PyErr_SetString(tstate, PyExc_RuntimeError, "DepthGuard-PVM: call-depth guard exceeded");
        return -1;
    }

    return 0;
}

void
_Py_DepthGuard_Leave(PyThreadState *tstate)
{
    if (_depthguard.current_depth > 0) {
        _depthguard.current_depth--;
    }
}

void
_Py_DepthGuard_SetWarn(int depth)
{
    _depthguard.warn_depth = (depth < 0) ? 0 : depth;
}

int
_Py_DepthGuard_GetWarn(void)
{
    return _depthguard.warn_depth;
}

void
_Py_DepthGuard_SetGuard(int depth)
{
    _depthguard.max_depth = (depth < 0) ? 0 : depth;
}

int
_Py_DepthGuard_GetGuard(void)
{
    return _depthguard.max_depth;
}

PyObject *
_Py_DepthGuard_GetStats(void)
{
    PyObject *dict = PyDict_New();
    if (!dict) {
        return NULL;
    }
    PyObject *v;

#define SET_STAT(key, val) do { \\
    v = PyLong_FromLong(val); \\
    if (!v || PyDict_SetItemString(dict, key, v) < 0) { \\
        Py_XDECREF(v); \\
        Py_DECREF(dict); \\
        return NULL; \\
    } \\
    Py_DECREF(v); \\
} while (0)

    SET_STAT("current_depth", _depthguard.current_depth);
    SET_STAT("max_depth_reached", _depthguard.max_depth_reached);
    SET_STAT("warnings_emitted", _depthguard.warnings_emitted);
    SET_STAT("warn_depth", _depthguard.warn_depth);
    SET_STAT("max_depth", _depthguard.max_depth);

#undef SET_STAT

    return dict;
}

void
_Py_DepthGuard_ResetStats(void)
{
    _depthguard.max_depth_reached = _depthguard.current_depth;
    _depthguard.warnings_emitted = 0;
}

int _Py_CheckRecursiveCallPy(
    PyThreadState *tstate)"""

path_ceval = os.path.join(base_dir, "Python/ceval.c")
if os.path.isfile(path_ceval):
    with open(path_ceval, "r") as f:
        content_ceval = f.read()
    if marker_ceval in content_ceval:
        content_ceval = content_ceval.replace(marker_ceval, depthguard_impl, 1)
        with open(path_ceval, "w") as f:
            f.write(content_ceval)
        print("  [+] Successfully patched Python/ceval.c")
    else:
        print("  [*] Python/ceval.c: Target marker already patched or not found.")


# =============================================================================
# 3. Python/ceval_macros.h
# =============================================================================
# -----------------------------------------------------------------------------
# EXACT ORIGINAL CPYTHON CODE (ceval_macros.h):
# -----------------------------------------------------------------------------
# static inline int _Py_EnterRecursivePy(PyThreadState *tstate) {
#     return (tstate->py_recursion_remaining-- <= 0) &&
#         _Py_CheckRecursiveCallPy(tstate);
# }
# 
# static inline void _Py_LeaveRecursiveCallPy(PyThreadState *tstate)  {
#     tstate->py_recursion_remaining++;
# }
# -----------------------------------------------------------------------------
# MODIFIED CODE INTERCEPTING ENTER AND LEAVE:
# -----------------------------------------------------------------------------
old_macros = """static inline int _Py_EnterRecursivePy(PyThreadState *tstate) {
    return (tstate->py_recursion_remaining-- <= 0) &&
        _Py_CheckRecursiveCallPy(tstate);
}

static inline void _Py_LeaveRecursiveCallPy(PyThreadState *tstate)  {
    tstate->py_recursion_remaining++;
}"""

new_macros = """static inline int _Py_EnterRecursivePy(PyThreadState *tstate) {
    tstate->py_recursion_remaining--;
    if (_Py_DepthGuard_Enter(tstate) < 0) {
        return -1;
    }
    if (tstate->py_recursion_remaining <= 0) {
        return _Py_CheckRecursiveCallPy(tstate);
    }
    return 0;
}

static inline void _Py_LeaveRecursiveCallPy(PyThreadState *tstate)  {
    _Py_DepthGuard_Leave(tstate);
    tstate->py_recursion_remaining++;
}"""

path_macros = os.path.join(base_dir, "Python/ceval_macros.h")
if os.path.isfile(path_macros):
    with open(path_macros, "r") as f:
        content_macros = f.read()
    if old_macros in content_macros:
        content_macros = content_macros.replace(old_macros, new_macros, 1)
        with open(path_macros, "w") as f:
            f.write(content_macros)
        print("  [+] Successfully patched Python/ceval_macros.h")
    else:
        print("  [*] Python/ceval_macros.h: Target macros already patched or not found.")


# =============================================================================
# 4. Python/sysmodule.c
# =============================================================================
# -----------------------------------------------------------------------------
# EXACT ORIGINAL CPYTHON CODE (sysmodule.c):
# -----------------------------------------------------------------------------
# static PyMethodDef sys_methods[] = {
# ...
#     {NULL, NULL}  // sentinel
# };
# -----------------------------------------------------------------------------
# MODIFIED CODE ADDING DEPTHGUARD SYS BUILTINS:
# -----------------------------------------------------------------------------
marker_sys_methods = "static PyMethodDef sys_methods[] = {"

sys_depthguard_funcs = """/* ========================================================================= */
/* --- DepthGuard-PVM sys Builtin Method Implementations ------------------- */
/* ========================================================================= */

static PyObject *
sys_set_depth_warn(PyObject *self, PyObject *arg)
{
    long depth = PyLong_AsLong(arg);
    if (depth == -1 && PyErr_Occurred()) {
        return NULL;
    }
    if (depth < 0) {
        PyErr_SetString(PyExc_ValueError, "warn depth must be >= 0");
        return NULL;
    }
    _Py_DepthGuard_SetWarn((int)depth);
    Py_RETURN_NONE;
}

static PyObject *
sys_get_depth_warn(PyObject *self, PyObject *Py_UNUSED(args))
{
    return PyLong_FromLong(_Py_DepthGuard_GetWarn());
}

static PyObject *
sys_set_depth_guard(PyObject *self, PyObject *arg)
{
    long depth = PyLong_AsLong(arg);
    if (depth == -1 && PyErr_Occurred()) {
        return NULL;
    }
    if (depth < 0) {
        PyErr_SetString(PyExc_ValueError, "max depth must be >= 0");
        return NULL;
    }
    _Py_DepthGuard_SetGuard((int)depth);
    Py_RETURN_NONE;
}

static PyObject *
sys_get_depth_guard(PyObject *self, PyObject *Py_UNUSED(args))
{
    return PyLong_FromLong(_Py_DepthGuard_GetGuard());
}

static PyObject *
sys_get_depth_stats(PyObject *self, PyObject *Py_UNUSED(args))
{
    return _Py_DepthGuard_GetStats();
}

static PyObject *
sys_reset_depth_stats(PyObject *self, PyObject *Py_UNUSED(args))
{
    _Py_DepthGuard_ResetStats();
    Py_RETURN_NONE;
}

static PyMethodDef sys_methods[] = {"""

marker_sentinel = "{NULL, NULL}  // sentinel\n};"
sys_depthguard_entries = """    {"set_depth_warn", _PyCFunction_CAST(sys_set_depth_warn), METH_O, "Set the call-depth warning threshold (0 to disable)."},
    {"get_depth_warn", _PyCFunction_CAST(sys_get_depth_warn), METH_NOARGS, "Get the call-depth warning threshold."},
    {"set_depth_guard", _PyCFunction_CAST(sys_set_depth_guard), METH_O, "Set the hard call-depth guard limit (0 to disable)."},
    {"get_depth_guard", _PyCFunction_CAST(sys_get_depth_guard), METH_NOARGS, "Get the hard call-depth guard limit."},
    {"get_depth_stats", _PyCFunction_CAST(sys_get_depth_stats), METH_NOARGS, "Get call-depth tracking statistics dict."},
    {"reset_depth_stats", _PyCFunction_CAST(sys_reset_depth_stats), METH_NOARGS, "Reset call-depth statistics."},
    {NULL, NULL}  // sentinel
};"""

path_sys = os.path.join(base_dir, "Python/sysmodule.c")
if os.path.isfile(path_sys):
    with open(path_sys, "r") as f:
        content_sys = f.read()
    if marker_sys_methods in content_sys:
        content_sys = content_sys.replace(marker_sys_methods, sys_depthguard_funcs, 1)
    if marker_sentinel in content_sys:
        content_sys = content_sys.replace(marker_sentinel, sys_depthguard_entries, 1)
        with open(path_sys, "w") as f:
            f.write(content_sys)
        print("  [+] Successfully patched Python/sysmodule.c")
    else:
        print("  [*] Python/sysmodule.c: Target sentinel already patched or not found.")

print("[DepthGuard Patcher] Patch operation complete.")
