"""
User CRUD API endpoints (F008).
Provides endpoints for user information management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from dependencies import get_db
from schemas.user import UserResponse, UserUpdate
from crud import user as user_crud

router = APIRouter()


@router.get("/{line_user_id}", response_model=UserResponse)
async def get_user(line_user_id: str, db: Session = Depends(get_db)):
    """
    Get user information by LINE user ID.
    
    Args:
        line_user_id: LINE user ID
        db: Database session
        
    Returns:
        User information
        
    Raises:
        404: User not found
    """
    user = user_crud.get_user_by_line_id(db, line_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{line_user_id}", response_model=UserResponse)
async def update_user(
    line_user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user information.
    
    Args:
        line_user_id: LINE user ID
        user_data: Fields to update
        db: Database session
        
    Returns:
        Updated user information
        
    Raises:
        404: User not found
    """
    user = user_crud.get_user_by_line_id(db, line_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = user_crud.update_user(db, user, user_data)
    return updated_user


@router.delete("/{line_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(line_user_id: str, db: Session = Depends(get_db)):
    """
    Delete a user by LINE user ID.
    
    Args:
        line_user_id: LINE user ID
        db: Database session
        
    Raises:
        404: User not found
    """
    user = user_crud.get_user_by_line_id(db, line_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_crud.delete_user(db, user)
    return None


@router.get("/{line_user_id}/calendar-status")
async def get_calendar_status(line_user_id: str, db: Session = Depends(get_db)):
    """
    Check if user has connected Google Calendar.
    
    Args:
        line_user_id: LINE user ID
        db: Database session
        
    Returns:
        Calendar connection status
    """
    user = user_crud.get_user_by_line_id(db, line_user_id)
    
    if not user:
        return {
            "isConnected": False,
            "email": None,
            "message": "User not found"
        }
    
    return {
        "isConnected": user.calendar_connected,
        "email": user.email,
        "message": "Connected" if user.calendar_connected else "Not connected"
    }
