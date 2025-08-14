"""Data models for the in-memory repository."""
from dataclasses import dataclass


@dataclass
class Target:
    ip: str


@dataclass
class ScanRun:
    id: int = 0


@dataclass
class Batch:
    id: int = 0


@dataclass
class Job:
    id: int = 0


@dataclass
class Result:
    id: int = 0
