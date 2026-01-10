"""
Vote API endpoints.
Handles poll voting operations.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db.poll_responses import (
    save_poll_responses,
    get_poll_responses,
    get_response_summary,
    delete_user_responses
)

vote_router = APIRouter(tags=["votes"])


class VoteItem(BaseModel):
    """Single vote item"""
    date: str = Field(..., description="Selected date label (e.g., '1月12日(月) 19:00–21:00')")
    start_time: Optional[str] = Field(None, description="Start time in ISO format")
    end_time: Optional[str] = Field(None, description="End time in ISO format")
    is_late: bool = Field(False, description="Whether the user might be late")


class VoteRequest(BaseModel):
    """Vote submission request"""
    line_user_id: str = Field(..., min_length=1, description="LINE user ID")
    session_id: Optional[int] = Field(None, description="Poll session ID")
    votes: List[VoteItem] = Field(..., description="List of selected dates")


class VoteResponse(BaseModel):
    """Vote submission response"""
    success: bool
    message: str
    saved_count: int


@vote_router.post("/api/events/vote", response_model=VoteResponse)
async def submit_vote(request: VoteRequest):
    """
    Submit poll votes for a user.
    
    This endpoint handles the "replace" logic:
    - Deletes all existing votes for the user (within the same session)
    - Inserts the new votes
    
    Request body:
    - line_user_id: LINE user ID (required)
    - session_id: Optional poll session ID
    - votes: Array of vote objects with date, start_time, end_time, is_late
    
    Returns:
    - success: Whether the operation succeeded
    - message: Status message
    - saved_count: Number of votes saved
    """
    if not request.line_user_id:
        raise HTTPException(status_code=400, detail="line_user_id is required")
    
    if not request.votes:
        raise HTTPException(status_code=400, detail="At least one vote is required")
    
    try:
        # Convert VoteItem objects to dictionaries
        votes_data = [
            {
                'date': vote.date,
                'start_time': vote.start_time,
                'end_time': vote.end_time,
                'is_late': vote.is_late
            }
            for vote in request.votes
        ]
        
        # Save votes (this replaces existing votes for the user)
        saved_count = save_poll_responses(
            line_user_id=request.line_user_id,
            votes=votes_data,
            session_id=request.session_id
        )
        
        return VoteResponse(
            success=True,
            message=f"Successfully saved {saved_count} vote(s)",
            saved_count=saved_count
        )
    
    except Exception as e:
        print(f"Error saving votes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save votes: {str(e)}"
        )


@vote_router.get("/api/events/votes")
async def get_votes(
    line_user_id: Optional[str] = None,
    session_id: Optional[int] = None
):
    """
    Get poll votes, optionally filtered by user or session.
    
    Query parameters:
    - line_user_id: Optional LINE user ID to filter by
    - session_id: Optional session ID to filter by
    
    Returns list of vote records.
    """
    try:
        responses = get_poll_responses(
            line_user_id=line_user_id,
            session_id=session_id
        )
        
        # Convert datetime objects to ISO strings for JSON serialization
        serialized = []
        for r in responses:
            item = dict(r)
            if item.get('start_time'):
                item['start_time'] = item['start_time'].isoformat()
            if item.get('end_time'):
                item['end_time'] = item['end_time'].isoformat()
            if item.get('created_at'):
                item['created_at'] = item['created_at'].isoformat()
            if item.get('updated_at'):
                item['updated_at'] = item['updated_at'].isoformat()
            serialized.append(item)
        
        return {
            "success": True,
            "votes": serialized,
            "count": len(serialized)
        }
    
    except Exception as e:
        print(f"Error fetching votes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch votes: {str(e)}"
        )


@vote_router.get("/api/events/votes/summary")
async def get_votes_summary(session_id: Optional[int] = None):
    """
    Get a summary of poll votes.
    
    Query parameters:
    - session_id: Optional session ID to filter by
    
    Returns:
    - total_voters: Number of unique voters
    - vote_counts: Dictionary mapping date labels to vote counts
    - voters_by_option: Dictionary mapping date labels to voter lists
    """
    try:
        summary = get_response_summary(session_id=session_id)
        return {
            "success": True,
            **summary
        }
    
    except Exception as e:
        print(f"Error fetching vote summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch vote summary: {str(e)}"
        )


@vote_router.delete("/api/events/votes/{line_user_id}")
async def delete_votes(line_user_id: str, session_id: Optional[int] = None):
    """
    Delete all votes for a user.
    
    Path parameters:
    - line_user_id: LINE user ID
    
    Query parameters:
    - session_id: Optional session ID to filter by
    
    Returns:
    - success: Whether the operation succeeded
    - deleted_count: Number of deleted votes
    """
    try:
        deleted_count = delete_user_responses(
            line_user_id=line_user_id,
            session_id=session_id
        )
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} vote(s)",
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        print(f"Error deleting votes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete votes: {str(e)}"
        )
