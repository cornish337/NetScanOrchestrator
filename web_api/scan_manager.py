"""Manages active scan tasks and their communication queues."""

import asyncio
from typing import Dict, Any, Optional


class ScanManager:
    """A singleton-like class to manage scan tasks in memory."""

    def __init__(self):
        # {scan_id: {"task": asyncio.Task, "queue": asyncio.Queue}}
        self.active_scans: Dict[str, Dict[str, Any]] = {}

    def register_scan(self, scan_id: str, task: asyncio.Task, queue: asyncio.Queue):
        """Stores a new scan task and its queue."""
        self.active_scans[scan_id] = {"task": task, "queue": queue}

    def deregister_scan(self, scan_id: str):
        """Removes a scan from the registry, typically upon completion."""
        if scan_id in self.active_scans:
            # Optionally, one might want to cancel the task here if it's still running
            # task = self.active_scans[scan_id].get("task")
            # if task and not task.done():
            #     task.cancel()
            del self.active_scans[scan_id]

    def get_scan_queue(self, scan_id: str) -> Optional[asyncio.Queue]:
        """Retrieves the queue for a given scan ID."""
        scan_info = self.active_scans.get(scan_id)
        return scan_info.get("queue") if scan_info else None

    def is_scan_active(self, scan_id: str) -> bool:
        """Checks if a scan is currently in the registry."""
        return scan_id in self.active_scans


# Create a single, globally-accessible instance of the manager.
scan_manager = ScanManager()
