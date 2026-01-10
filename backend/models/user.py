from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    picture_url = Column(String(512), nullable=True)
    status_message = Column(String(255), nullable=True)
    google_connected = Column(Boolean, default=False)
    google_access_token = Column(String(1024), nullable=True)
    google_refresh_token = Column(String(1024), nullable=True)
    google_token_expiry = Column(DateTime, nullable=True)
    google_token_type = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
