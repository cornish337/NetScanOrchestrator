from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./netscan.db"

# The connect_args parameter is specific to SQLite. It ensures that the same thread check is disabled
# because some environments (like web frameworks or CLI tools) may use threading.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


# Run the initialization on module import so that the database schema is ready as soon as the
# application starts.
init_db()
