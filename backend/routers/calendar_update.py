"""
Calendar event update endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from db import get_connection
from services.google_calendar_service import create_event_for_session

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class CreateEventWithRestaurantRequest(BaseModel):
    """Request body for creating calendar event with restaurant info"""
    restaurant_name: str
    restaurant_url: Optional[str] = None
    reservation_notes: Optional[str] = None


@router.get("/sessions/{session_id}/events")
async def get_session_events(session_id: int):
    """
    Get all calendar events for a session
    
    Args:
        session_id: Poll session ID
        
    Returns:
        List of calendar events
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        query = """
            SELECT ce.id, ce.google_event_id, ce.title, ce.description,
                   ce.start_time, ce.end_time, ce.location, ce.synced,
                   ce.created_at, ce.updated_at,
                   u.line_user_id, lu.display_name
            FROM calendar_events ce
            JOIN users u ON ce.user_id = u.id
            LEFT JOIN line_users lu ON u.line_user_id = lu.line_user_id
            WHERE ce.description LIKE %s
            ORDER BY ce.created_at DESC
        """
        cursor.execute(query, (f"session_id:{session_id}%",))
        events = cursor.fetchall()
        
        return {
            "session_id": session_id,
            "events": events,
            "total": len(events)
        }
        
    finally:
        cursor.close()
        connection.close()

@router.post("/sessions/{session_id}/create-with-restaurant")
async def create_event_with_restaurant(
    session_id: int,
    request: CreateEventWithRestaurantRequest
):
    """
    Create calendar events after restaurant is confirmed.
    This is called after the restaurant selection voting and reservation confirmation.
    
    Args:
        session_id: Poll session ID
        request: Restaurant info and optional reservation notes
        
    Returns:
        Created events information
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get session info to retrieve finalized date/time
        session_query = """
            SELECT id, finalized_date, finalized_start_time, finalized_end_time, 
                   topic, event_registered
            FROM poll_sessions 
            WHERE id = %s
        """
        cursor.execute(session_query, (session_id,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("event_registered"):
            raise HTTPException(
                status_code=400,
                detail="Calendar events already created for this session"
            )
        
        # Extract date/time information
        event_title = session.get("topic", "飲み会")
        date_label = session.get("finalized_date")
        start_time = str(session.get("finalized_start_time"))
        end_time = str(session.get("finalized_end_time"))
        location = request.restaurant_name
        
        if not date_label or not start_time or not end_time:
            raise HTTPException(
                status_code=400,
                detail="Session date/time not yet finalized"
            )
        
        # Create calendar events
        calendar_result = await create_event_for_session(
            session_id=session_id,
            event_title=event_title,
            date_label=date_label,
            start_time=start_time,
            end_time=end_time,
            location=location,
            description_extra=request.reservation_notes or ""
        )
        
        # Update session with restaurant info
        update_query = """
            UPDATE poll_sessions
            SET restaurant_name = %s,
                restaurant_url = %s,
                reservation_confirmed = TRUE,
                event_registered = TRUE
            WHERE id = %s
        """
        cursor.execute(update_query, (
            request.restaurant_name,
            request.restaurant_url,
            session_id
        ))
        connection.commit()
        
        return {
            "success": True,
            "session_id": session_id,
            "restaurant_name": request.restaurant_name,
            "restaurant_url": request.restaurant_url,
            "calendar_creation": calendar_result,
            "message": f"{request.restaurant_name}で予約確定！カレンダーに自動登録しました。"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()