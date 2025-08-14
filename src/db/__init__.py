"""In-memory data store for NetScanOrchestrator."""
from .repository import add_targets, get_targets  # re-export for convenience

__all__ = ["add_targets", "get_targets"]
