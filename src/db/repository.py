"""Simple in-memory repository for storing scan targets and results."""
from __future__ import annotations

from typing import List

from .models import Target, ScanRun, Batch, Job, Result

# In-memory stores
_TARGETS: List[Target] = []


def add_targets(ips: List[str]) -> int:
    """Add a list of IP strings as Targets to the repository."""
    for ip in ips:
        _TARGETS.append(Target(ip=ip))
    return len(ips)


def get_targets() -> List[Target]:
    """Return all stored Targets."""
    return list(_TARGETS)
