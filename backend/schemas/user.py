from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    line_user_id: str = Field(..., max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    picture_url: Optional[str] = Field(None, max_length=512)
    status_message: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    picture_url: Optional[str] = Field(None, max_length=512)
    status_message: Optional[str] = Field(None, max_length=255)
    google_connected: Optional[bool] = None


class UserGoogleAuth(BaseModel):
    google_access_token: str
    google_refresh_token: Optional[str] = None
    google_token_expiry: datetime
    google_token_type: Optional[str] = None
    google_connected: bool = True


class UserInDBBase(UserBase):
    id: int
    google_connected: bool = False
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    google_token_expiry: Optional[datetime] = None
    google_token_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass
