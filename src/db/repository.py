"""Convenience CRUD helpers for database models."""

from __future__ import annotations

from typing import Iterable, List, Optional, Type, TypeVar, Any

from sqlalchemy.orm import Session

from db.models import Target, ScanRun, Batch, Job, Result

ModelType = TypeVar("ModelType", Target, ScanRun, Batch, Job, Result)


def _create(session: Session, model: Type[ModelType], **kwargs: Any) -> ModelType:
    instance = model(**kwargs)
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


def _get(session: Session, model: Type[ModelType], obj_id: int) -> Optional[ModelType]:
    return session.get(model, obj_id)


def _list(session: Session, model: Type[ModelType]) -> List[ModelType]:
    return session.query(model).all()


def _update(session: Session, model: Type[ModelType], obj_id: int, **kwargs: Any) -> Optional[ModelType]:
    instance = _get(session, model, obj_id)
    if not instance:
        return None
    for key, value in kwargs.items():
        setattr(instance, key, value)
    session.commit()
    return instance


def _delete(session: Session, model: Type[ModelType], obj_id: int) -> bool:
    instance = _get(session, model, obj_id)
    if not instance:
        return False
    session.delete(instance)
    session.commit()
    return True


# Target CRUD ---------------------------------------------------------------

def create_target(session: Session, **kwargs: Any) -> Target:
    return _create(session, Target, **kwargs)


def get_target(session: Session, target_id: int) -> Optional[Target]:
    return _get(session, Target, target_id)


def get_target_by_address(session: Session, address: str) -> Optional[Target]:
    return session.query(Target).filter(Target.address == address).first()


def list_targets(session: Session) -> List[Target]:
    return _list(session, Target)


def update_target(session: Session, target_id: int, **kwargs: Any) -> Optional[Target]:
    return _update(session, Target, target_id, **kwargs)


def delete_target(session: Session, target_id: int) -> bool:
    return _delete(session, Target, target_id)


# ScanRun CRUD --------------------------------------------------------------

def create_scan_run(session: Session, **kwargs: Any) -> ScanRun:
    return _create(session, ScanRun, **kwargs)


def get_scan_run(session: Session, run_id: int) -> Optional[ScanRun]:
    return _get(session, ScanRun, run_id)


def list_scan_runs(session: Session) -> List[ScanRun]:
    return _list(session, ScanRun)


def update_scan_run(session: Session, run_id: int, **kwargs: Any) -> Optional[ScanRun]:
    return _update(session, ScanRun, run_id, **kwargs)


def delete_scan_run(session: Session, run_id: int) -> bool:
    return _delete(session, ScanRun, run_id)


# Batch CRUD ---------------------------------------------------------------

def create_batch(session: Session, **kwargs: Any) -> Batch:
    return _create(session, Batch, **kwargs)


def get_batch(session: Session, batch_id: int) -> Optional[Batch]:
    return _get(session, Batch, batch_id)


def list_batches(session: Session) -> List[Batch]:
    return _list(session, Batch)


def list_batches_for_run(session: Session, scan_run_id: int) -> List[Batch]:
    """Return all Batches for a given ScanRun."""
    return session.query(Batch).filter(Batch.scan_run_id == scan_run_id).all()


def update_batch(session: Session, batch_id: int, **kwargs: Any) -> Optional[Batch]:
    return _update(session, Batch, batch_id, **kwargs)


def delete_batch(session: Session, batch_id: int) -> bool:
    return _delete(session, Batch, batch_id)


# Job CRUD -----------------------------------------------------------------

def create_job(session: Session, **kwargs: Any) -> Job:
    return _create(session, Job, **kwargs)


def get_job(session: Session, job_id: int) -> Optional[Job]:
    return _get(session, Job, job_id)


def list_jobs(session: Session) -> List[Job]:
    return _list(session, Job)


def update_job(session: Session, job_id: int, **kwargs: Any) -> Optional[Job]:
    return _update(session, Job, job_id, **kwargs)


def delete_job(session: Session, job_id: int) -> bool:
    return _delete(session, Job, job_id)


# Result CRUD --------------------------------------------------------------

def create_result(session: Session, **kwargs: Any) -> Result:
    return _create(session, Result, **kwargs)


def get_result(session: Session, result_id: int) -> Optional[Result]:
    return _get(session, Result, result_id)


def list_results(session: Session) -> List[Result]:
    return _list(session, Result)


def update_result(session: Session, result_id: int, **kwargs: Any) -> Optional[Result]:
    return _update(session, Result, result_id, **kwargs)


def delete_result(session: Session, result_id: int) -> bool:
    return _delete(session, Result, result_id)
