from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    display_name = Column(String(255), nullable=True)
    picture_url = Column(String(512), nullable=True)
    status_message = Column(String(255), nullable=True)
    access_token = Column(String(1024), nullable=True)  # Google access token
    refresh_token = Column(String(1024), nullable=True)  # Google refresh token
    token_expiry = Column(DateTime, nullable=True)  # Google token expiry
    calendar_connected = Column(Boolean, default=False)  # Google calendar connected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
