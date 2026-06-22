from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.models import Base

engine = create_engine(
    "sqlite:///./jarvis.db",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and close it when done."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
