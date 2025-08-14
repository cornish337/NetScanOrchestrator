"""Database session and engine management."""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from .models import Base

DEFAULT_DB_PATH = os.path.join(".netscan_orchestrator", "state.db")

_engine = None  # type: ignore
_SessionFactory = None  # type: ignore


def init_engine(db_path: Optional[str] = None):
    """Initialise the SQLAlchemy engine and create tables if required."""
    global _engine, _SessionFactory
    if _engine is not None:
        return _engine

    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    url = f"sqlite:///{path}"
    _engine = create_engine(url, connect_args={"check_same_thread": False})
    _SessionFactory = scoped_session(sessionmaker(bind=_engine))

    # Create tables on first use
    Base.metadata.create_all(_engine)
    return _engine


def get_session(db_path: Optional[str] = None) -> Session:
    """Return a new SQLAlchemy session, initialising the engine if needed."""
    if _engine is None:
        init_engine(db_path)
    assert _SessionFactory is not None  # for type checkers
    return _SessionFactory()
