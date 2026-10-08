"""Structured diagnostics and presentation helpers for Harnessmith."""

from .rendering import (
    diagnostic_to_dict,
    diagnostics_fail_threshold,
    render_diagnostics_json,
    render_diagnostics_sarif,
    render_diagnostics_text,
)
from .rules import analyze_audit_diagnostics

__all__ = [
    "analyze_audit_diagnostics",
    "diagnostic_to_dict",
    "diagnostics_fail_threshold",
    "render_diagnostics_json",
    "render_diagnostics_sarif",
    "render_diagnostics_text",
]
