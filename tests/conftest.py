import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from web_api.app import app
from web_api.deps import get_db
from src.db.session import Base, init_engine as init_global_engine

@pytest.fixture(scope="function")
def test_db_session():
    """
    Pytest fixture to create a temporary, isolated database for a test function.
    It overrides the FastAPI `get_db` dependency.
    """
    # Create a temporary file for the database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    # Use a separate engine for the test DB
    engine = create_engine(f"sqlite:///{db_path}")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        """Dependency override to use the temporary database."""
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    # Apply the override
    app.dependency_overrides[get_db] = override_get_db

    # Yield a session for the test to use if needed, though the override is the main point
    yield TestingSessionLocal()

    # Teardown: remove the override and close/delete the DB
    app.dependency_overrides.clear()
    os.close(db_fd)
    os.unlink(db_path)
