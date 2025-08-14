import os
import sqlite3
from typing import Optional

from src.config import STATE_DB_PATH as DEFAULT_STATE_DB_PATH


def _resolve_path(override_path: Optional[str] = None) -> str:
    """Return the state DB path from env var, override, or default."""
    if override_path:
        return override_path
    return os.environ.get("STATE_DB_PATH", DEFAULT_STATE_DB_PATH)


def create_session(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a connection to the state database.

    The path can be provided directly, via the STATE_DB_PATH environment variable,
    or falls back to the default defined in :mod:`src.config`.
    """
    path = _resolve_path(db_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return sqlite3.connect(path)
