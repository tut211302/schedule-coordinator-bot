from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    line_user_id: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    picture_url: Optional[str] = Field(None, max_length=512)
    status_message: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    line_user_id: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    picture_url: Optional[str] = Field(None, max_length=512)
    status_message: Optional[str] = Field(None, max_length=255)
    calendar_connected: Optional[bool] = None


class UserGoogleAuth(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_expiry: datetime
    calendar_connected: bool = True


class UserInDBBase(UserBase):
    id: int
    google_id: Optional[str] = None
    calendar_connected: bool = False
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass
