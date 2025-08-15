"""FastAPI dependencies."""

from typing import Generator, Any

from sqlalchemy.orm import Session

from src.db.session import get_session


def get_db() -> Generator[Session, Any, None]:
    """
    FastAPI dependency that provides a SQLAlchemy session.

    It ensures that the database session is always closed after the request,
    even if an error occurs.
    """
    db = None
    try:
        db = get_session()
        yield db
    finally:
        if db:
            db.close()
