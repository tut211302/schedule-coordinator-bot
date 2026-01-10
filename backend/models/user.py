"""
User model for database operations.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """
    User model representing a user who connects via LINE and optionally Google Calendar.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # LINE related fields
    line_user_id = Column(String(255), unique=True, index=True, nullable=True)
    line_display_name = Column(String(255), nullable=True)
    line_picture_url = Column(Text, nullable=True)
    
    # Google related fields
    email = Column(String(255), unique=True, index=True, nullable=True)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    calendar_connected = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, line_user_id={self.line_user_id}, email={self.email})>"
