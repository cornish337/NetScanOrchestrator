import pytest
from fastapi.testclient import TestClient
import sys
import os
import tempfile
import subprocess

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_api.app import app
from src.db.session import init_engine, get_session
from web_api.deps import get_db

@pytest.fixture(scope="function")
def temp_db_path():
    """Create a temporary SQLite database file and yield its path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    db_path = tmp.name
    yield db_path
    os.unlink(db_path)

@pytest.fixture(scope="function")
def db_session(temp_db_path):
    """
    Creates a new database session for a test, ensuring the engine is
    re-initialized to the test-specific database.
    """
    from src.db import session as db_session_module
    db_session_module._engine = None  # Force re-initialization
    init_engine(temp_db_path)
    session = get_session()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client_with_db(db_session):
    """FastAPI TestClient that uses the isolated, temporary database for the session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def cli_runner():
    """Fixture to provide a helper function for running CLI commands."""
    def run_cli(*args, db_path: str):
        cmd = ["netscan", "--db-path", db_path, *map(str, args)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            pytest.fail(f"CLI command {' '.join(cmd)} failed with exit code {result.returncode}")
        return result.stdout.strip()
    return run_cli
