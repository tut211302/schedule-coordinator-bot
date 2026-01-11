"""
Deadline API endpoints.
Handles voting deadline operations.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db.deadline import (
    create_deadline,
    get_deadline,
    get_or_create_deadline,
    check_deadline_expired,
    delete_deadline,
    DEFAULT_DEADLINE_MINUTES
)


deadline_router = APIRouter(tags=["deadline"])


class CreateDeadlineRequest(BaseModel):
    """Request model for creating a deadline."""
    session_id: int = Field(..., description="Poll session ID")
    group_id: Optional[str] = Field(None, description="LINE group ID")
    deadline_minutes: Optional[int] = Field(
        None, 
        description=f"Minutes until deadline (default: {DEFAULT_DEADLINE_MINUTES})"
    )


class DeadlineResponse(BaseModel):
    """Response model for deadline info."""
    session_id: int
    group_id: Optional[str]
    deadline: Optional[str]
    is_expired: bool
    remaining_seconds: int
    created_at: Optional[str]


@deadline_router.post("/api/events/deadline")
async def create_session_deadline(request: CreateDeadlineRequest):
    """
    Create or update a deadline for a session.
    
    If a deadline already exists for the session, it will be updated.
    """
    try:
        result = create_deadline(
            session_id=request.session_id,
            group_id=request.group_id,
            deadline_minutes=request.deadline_minutes
        )
        return {
            "success": True,
            "message": "Deadline created successfully",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@deadline_router.get("/api/events/deadline/{session_id}")
async def get_session_deadline(session_id: int):
    """
    Get deadline information for a session.
    
    Returns deadline info including whether it has expired and remaining time.
    """
    try:
        deadline_info = get_deadline(session_id)
        
        if not deadline_info:
            return {
                "success": True,
                "has_deadline": False,
                "session_id": session_id,
                "deadline": None,
                "is_expired": False,
                "remaining_seconds": -1  # -1 indicates no deadline
            }
        
        return {
            "success": True,
            "has_deadline": True,
            **deadline_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@deadline_router.get("/api/events/deadline/{session_id}/check")
async def check_deadline(session_id: int):
    """
    Quick check if the deadline has expired.
    
    Returns:
        - is_expired: True if deadline has passed
        - can_vote: True if voting is still allowed
    """
    try:
        is_expired = check_deadline_expired(session_id)
        return {
            "session_id": session_id,
            "is_expired": is_expired,
            "can_vote": not is_expired
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@deadline_router.post("/api/events/deadline/{session_id}/ensure")
async def ensure_deadline(
    session_id: int,
    group_id: Optional[str] = None,
    deadline_minutes: Optional[int] = None,
    reset_if_expired: Optional[bool] = None
):
    """
    Ensure a deadline exists for a session.
    
    If no deadline exists, creates one. Otherwise returns existing deadline.
    Useful when opening the poll page to ensure a deadline is set.
    
    In dev mode (DEV_MODE_RESET_EXPIRED=true), expired deadlines are automatically reset.
    In production mode, expired deadlines remain as-is (LINE Bot controls deadline).
    
    Args:
        reset_if_expired: Override the default behavior. 
                         True = reset expired deadlines (dev mode behavior)
                         False = keep expired deadlines (production behavior)
    """
    try:
        result = get_or_create_deadline(
            session_id=session_id,
            group_id=group_id,
            deadline_minutes=deadline_minutes,
            reset_if_expired=reset_if_expired
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@deadline_router.delete("/api/events/deadline/{session_id}")
async def remove_deadline(session_id: int):
    """
    Delete a deadline for a session.
    
    This allows voting without time restrictions.
    """
    try:
        deleted = delete_deadline(session_id)
        return {
            "success": True,
            "deleted": deleted,
            "message": "Deadline removed" if deleted else "No deadline found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
