import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default DSN targets the existing MySQL container; override via DATABASE_URL
def _build_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "mysql+mysqlconnector://root:password@localhost:3306/calendar_db",
    )


DATABASE_URL = _build_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()
