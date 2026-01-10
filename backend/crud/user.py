"""
CRUD operations for User model.
"""

from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserUpdate
from datetime import datetime
from typing import Optional


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by primary key ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_line_id(db: Session, line_user_id: str) -> Optional[User]:
    """Get user by LINE user ID."""
    return db.query(User).filter(User.line_user_id == line_user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user from LINE webhook data.
    
    Args:
        db: Database session
        user_data: UserCreate schema with LINE user info
        
    Returns:
        Created User instance
    """
    db_user = User(
        line_user_id=user_data.line_user_id,
        line_display_name=user_data.line_display_name,
        line_picture_url=user_data.line_picture_url,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    """
    Update user with provided data.
    Only updates fields that are not None.
    
    Args:
        db: Database session
        user: Existing User instance
        user_data: UserUpdate schema with fields to update
        
    Returns:
        Updated User instance
    """
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


def update_user_google_token(
    db: Session,
    user: User,
    google_id: str,
    email: str,
    access_token: str,
    refresh_token: Optional[str],
    token_expiry: Optional[datetime]
) -> User:
    """
    Update user's Google OAuth tokens after successful authentication.
    
    Args:
        db: Database session
        user: Existing User instance
        google_id: Google account ID
        email: Google email address
        access_token: OAuth access token
        refresh_token: OAuth refresh token (may be None on subsequent auths)
        token_expiry: Token expiration datetime
        
    Returns:
        Updated User instance
    """
    user.google_id = google_id
    user.email = email
    user.access_token = access_token
    
    # Refresh token is only provided on first authorization or if access_type='offline'
    if refresh_token:
        user.refresh_token = refresh_token
    
    user.token_expiry = token_expiry
    user.calendar_connected = True
    
    db.commit()
    db.refresh(user)
    return user


def disconnect_google(db: Session, user: User) -> User:
    """
    Disconnect user's Google Calendar integration.
    Clears all Google-related tokens.
    
    Args:
        db: Database session
        user: Existing User instance
        
    Returns:
        Updated User instance
    """
    user.access_token = None
    user.refresh_token = None
    user.token_expiry = None
    user.calendar_connected = False
    
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> bool:
    """
    Delete a user from database.
    
    Args:
        db: Database session
        user: User instance to delete
        
    Returns:
        True if deleted successfully
    """
    db.delete(user)
    db.commit()
    return True
