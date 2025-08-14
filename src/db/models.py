"""SQLAlchemy ORM models for the NetScanOrchestrator."""

from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Table,
    Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Association table for many-to-many relationship between batches and targets
batch_target_association = Table(
    "batch_target_association",
    Base.metadata,
    Column("batch_id", ForeignKey("batches.id"), primary_key=True),
    Column("target_id", ForeignKey("targets.id"), primary_key=True),
)


class Target(Base):
    """Represents a host or IP address that can be scanned."""

    __tablename__ = "targets"

    id = Column(Integer, primary_key=True)
    address = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    batches = relationship(
        "Batch",
        secondary=batch_target_association,
        back_populates="targets",
    )
    jobs = relationship("Job", back_populates="target")

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<Target id={self.id} address={self.address}>"


class ScanRun(Base):
    """A single invocation of the scanning process."""

    __tablename__ = "scan_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending", nullable=False)
    options = Column(String, nullable=True)  # e.g. nmap command line options

    jobs = relationship("Job", back_populates="scan_run")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ScanRun id={self.id} status={self.status}>"


class Batch(Base):
    """A collection of targets that can be scanned together."""

    __tablename__ = "batches"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    targets = relationship(
        "Target",
        secondary=batch_target_association,
        back_populates="batches",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Batch id={self.id} name={self.name}>"


class JobStatus(enum.Enum):
    """Possible execution states for a Job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Job(Base):
    """Represents a unit of work scanning a single target within a scan run."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    scan_run_id = Column(Integer, ForeignKey("scan_runs.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    pid = Column(Integer, nullable=True)
    command = Column(Text, default="", nullable=False)
    return_code = Column(Integer, nullable=True)
    timeout_sec = Column(Integer, nullable=True)
    status = Column(
        SAEnum(JobStatus, name="job_status"),
        default=JobStatus.PENDING,
        nullable=False,
    )
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    scan_run = relationship("ScanRun", back_populates="jobs")
    target = relationship("Target", back_populates="jobs")
    results = relationship("Result", back_populates="job")

    @property
    def duration(self) -> Optional[float]:
        """Return job runtime in seconds, if start and end times are known."""

        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Job id={self.id} target_id={self.target_id} status={self.status}>"


class Result(Base):
    """Stores the outcome of a job."""

    __tablename__ = "results"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("Job", back_populates="results")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Result id={self.id} job_id={self.job_id}>"
