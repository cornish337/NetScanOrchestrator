"""Pydantic models for the FastAPI web API."""

from enum import Enum
from typing import List, Dict, Any, Optional, Union

from pydantic import BaseModel


# Request/Response models for POST /api/scans
class ScanType(str, Enum):
    TCP = "TCP"
    UDP = "UDP"

class ScanRequest(BaseModel):
    targets: List[str]
    nmap_options: str
    scan_type: Optional[ScanType] = None


class ScanResponse(BaseModel):
    scan_id: str


# Status Enum for overall scan status
class ScanStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Models for GET /api/scans/{scan_id} response
class ScanProgress(BaseModel):
    total_chunks: int
    completed_chunks: int
    failed_chunks: int


class HostResult(BaseModel):
    status: str  # 'up' or 'down'
    ports: Optional[List[Any]] = None
    reason: Optional[str] = None


class ScanResults(BaseModel):
    hosts: Dict[str, HostResult]


class ScanStatusResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    progress: ScanProgress
    results: ScanResults


class ApiResponse(BaseModel):
    status: str = "success"
    data: Any


# WebSocket Message Models

class WebSocketMessageType(str, Enum):
    CHUNK_UPDATE = "CHUNK_UPDATE"
    SCAN_COMPLETE = "SCAN_COMPLETE"


# Note: Job statuses from the DB are lowercase, but API contract wants uppercase.
# We will handle this mapping in the application logic.
class ChunkStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STUCK = "STUCK" # Not a DB status, but defined in API contract


class ChunkUpdatePayload(BaseModel):
    chunk_id: str  # This will be the Job ID from the database
    status: ChunkStatus
    result: Optional[Any] = None  # Minimal result for the host


class ScanCompletePayload(BaseModel):
    scan_id: str
    status: ScanStatus  # Should be COMPLETED or FAILED
    final_results_url: str


class WebSocketMessage(BaseModel):
    type: WebSocketMessageType
    payload: Union[ChunkUpdatePayload, ScanCompletePayload]
