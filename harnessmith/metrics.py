"""Deterministic size metrics shared by compilation and auditing."""

from __future__ import annotations

import math


def estimate_tokens(text: str) -> int:
    """Estimate tokens using the documented four-characters-per-token proxy."""

    return int(math.ceil(len(text) / 4.0))
