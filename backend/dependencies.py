"""
FastAPI dependency injection functions.
"""

from database import SessionLocal
from typing import Generator
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    Creates a new session for each request and closes it when done.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
