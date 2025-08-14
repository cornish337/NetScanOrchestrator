from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path
from typing import List, Dict, Optional
import uuid


@dataclass
class Target:
    id: str
    value: str
    ingested_at: str


@dataclass
class ScanRun:
    id: str
    created_at: str
    status: str
    target_ids: List[str]


@dataclass
class Batch:
    id: str
    scan_run_id: str
    target_ids: List[str]
    created_at: str
    status: str


@dataclass
class Job:
    id: str
    batch_id: str
    started_at: str
    finished_at: Optional[str]
    status: str
    artifact: Optional[str]


class Repository:
    """Simple JSON file based repository for persisting run metadata."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.data: Dict[str, List[Dict]] = {
            "targets": [],
            "scan_runs": [],
            "batches": [],
            "jobs": [],
        }
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text()))
            except json.JSONDecodeError:
                # Corrupt or empty file - start fresh
                pass

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))

    # Creation helpers -------------------------------------------------
    def create_target(self, value: str) -> Target:
        target = Target(id=str(uuid.uuid4()), value=value, ingested_at=datetime.utcnow().isoformat())
        self.data["targets"].append(asdict(target))
        self._save()
        return target

    def create_scan_run(self, target_ids: List[str]) -> ScanRun:
        run = ScanRun(
            id=str(uuid.uuid4()),
            created_at=datetime.utcnow().isoformat(),
            status="planned",
            target_ids=target_ids,
        )
        self.data["scan_runs"].append(asdict(run))
        self._save()
        return run

    def create_batch(self, scan_run_id: str, target_ids: List[str]) -> Batch:
        batch = Batch(
            id=str(uuid.uuid4()),
            scan_run_id=scan_run_id,
            target_ids=target_ids,
            created_at=datetime.utcnow().isoformat(),
            status="pending",
        )
        self.data["batches"].append(asdict(batch))
        self._save()
        return batch

    def create_job(self, batch_id: str, artifact: Optional[str] = None, status: str = "completed") -> Job:
        now = datetime.utcnow().isoformat()
        job = Job(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            started_at=now,
            finished_at=now,
            status=status,
            artifact=artifact,
        )
        self.data["jobs"].append(asdict(job))
        self._save()
        return job

    # Retrieval helpers ------------------------------------------------
    def list_targets(self) -> List[Target]:
        return [Target(**t) for t in self.data["targets"]]

    def get_scan_run(self, run_id: str) -> Optional[ScanRun]:
        for r in self.data["scan_runs"]:
            if r["id"] == run_id:
                return ScanRun(**r)
        return None

    def list_batches(self, scan_run_id: str) -> List[Batch]:
        return [Batch(**b) for b in self.data["batches"] if b["scan_run_id"] == scan_run_id]

