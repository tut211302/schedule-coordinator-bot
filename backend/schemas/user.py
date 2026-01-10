"""
Pydantic schemas for User model validation and serialization.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base schema with common user attributes."""
    line_user_id: Optional[str] = None
    line_display_name: Optional[str] = None
    line_picture_url: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for creating a new user (from LINE webhook)."""
    line_user_id: str
    line_display_name: Optional[str] = None
    line_picture_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    line_display_name: Optional[str] = None
    line_picture_url: Optional[str] = None
    email: Optional[str] = None
    calendar_connected: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response with all public fields."""
    id: int
    line_user_id: Optional[str] = None
    line_display_name: Optional[str] = None
    line_picture_url: Optional[str] = None
    email: Optional[str] = None
    calendar_connected: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode


class GoogleAuthCallback(BaseModel):
    """Schema for Google OAuth callback request."""
    code: str
    state: str  # Contains line_user_id for user binding


class GoogleAuthResponse(BaseModel):
    """Schema for Google OAuth success response."""
    success: bool
    email: Optional[str] = None
    message: Optional[str] = None
