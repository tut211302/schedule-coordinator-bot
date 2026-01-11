"""
Google Calendar API service for creating and managing calendar events.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from db import get_connection


class GoogleCalendarService:
    """Service for interacting with Google Calendar API"""

    CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

    @staticmethod
    def _parse_datetime(date_str: str, time_str: str) -> str:
        """
        Parse date and time strings into RFC3339 format for Google Calendar API.
        
        Args:
            date_str: Date string (e.g., "2026-01-15" or "1月15日(水)")
            time_str: Time string (e.g., "18:00:00" or "18:00")
            
        Returns:
            RFC3339 formatted datetime string
        """
        try:
            # Handle time format
            if isinstance(time_str, str):
                time_parts = time_str.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            else:
                # Assume it's already a datetime.time object
                hour = time_str.hour
                minute = time_str.minute

            # Handle date format
            if "月" in date_str and "日" in date_str:
                # Japanese format: "1月15日(水)" -> extract numbers
                import re
                match = re.search(r'(\d+)月(\d+)日', date_str)
                if match:
                    month = int(match.group(1))
                    day = int(match.group(2))
                    year = datetime.now().year
                    dt = datetime(year, month, day, hour, minute)
                else:
                    raise ValueError(f"Cannot parse date: {date_str}")
            else:
                # ISO format: "2026-01-15"
                date_obj = datetime.fromisoformat(date_str.split('T')[0])
                dt = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)

            # Return in RFC3339 format with timezone
            return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        
        except Exception as e:
            raise ValueError(f"Failed to parse datetime: {date_str} {time_str} - {str(e)}")

    @staticmethod
    async def create_event(
        access_token: str,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """
        Create a new calendar event in Google Calendar.
        
        Args:
            access_token: Google OAuth access token
            summary: Event title/summary
            start_datetime: Start time in RFC3339 format
            end_datetime: End time in RFC3339 format
            description: Optional event description
            location: Optional event location
            attendees: Optional list of attendee email addresses
            calendar_id: Calendar ID (default: "primary")
            
        Returns:
            Created event object from Google Calendar API
            
        Raises:
            Exception: If event creation fails
        """
        url = f"{GoogleCalendarService.CALENDAR_API_BASE}/calendars/{calendar_id}/events"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        event_body = {
            "summary": summary,
            "start": {
                "dateTime": start_datetime,
                "timeZone": "Asia/Tokyo"
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": "Asia/Tokyo"
            }
        }
        
        if description:
            event_body["description"] = description
        
        if location:
            event_body["location"] = location
        
        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]
            event_body["guestsCanSeeOtherGuests"] = True
            event_body["guestsCanInviteOthers"] = False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=event_body) as resp:
                    if resp.status not in [200, 201]:
                        error_text = await resp.text()
                        raise Exception(
                            f"Calendar event creation failed: {resp.status} {error_text}"
                        )
                    
                    event_data = await resp.json()
                    return event_data
        
        except Exception as e:
            raise Exception(f"Failed to create calendar event: {str(e)}")

    @staticmethod
    async def get_user_tokens(line_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Google OAuth tokens for a LINE user.
        
        Args:
            line_user_id: LINE user ID
            
        Returns:
            Dict with access_token, refresh_token, token_expiry, email
            None if user not found or not connected to Google
        """
        query = """
            SELECT access_token, refresh_token, token_expiry, email, calendar_connected
            FROM users
            WHERE line_user_id = %s AND calendar_connected = TRUE
        """
        
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (line_user_id,))
            result = cursor.fetchone()
            
            if not result or not result.get("access_token"):
                return None
            
            return result

    @staticmethod
    async def get_all_connected_users(session_id: int) -> List[Dict[str, Any]]:
        """
        Get all users who have voted in a session AND have Google Calendar connected.
        
        Args:
            session_id: Poll session ID
            
        Returns:
            List of dicts with line_user_id, email, access_token, display_name
        """
        query = """
            SELECT DISTINCT 
                u.line_user_id,
                u.email,
                u.access_token,
                u.refresh_token,
                u.token_expiry,
                lu.display_name
            FROM poll_responses pr
            JOIN users u ON pr.line_user_id = u.line_user_id
            LEFT JOIN line_users lu ON pr.line_user_id = lu.line_user_id
            WHERE pr.session_id = %s 
              AND u.calendar_connected = TRUE
              AND u.access_token IS NOT NULL
        """
        
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (session_id,))
            return cursor.fetchall()

    @staticmethod
    def save_event_to_db(
        line_user_id: str,
        google_event_id: str,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> int:
        """
        Save created calendar event to database.
        
        Args:
            line_user_id: LINE user ID
            google_event_id: Google Calendar event ID
            title: Event title
            start_time: Start datetime string
            end_time: End datetime string
            description: Optional description
            location: Optional location
            
        Returns:
            Created event ID in database
        """
        # First get user's internal ID
        get_user_query = "SELECT id FROM users WHERE line_user_id = %s"
        
        insert_query = """
            INSERT INTO calendar_events 
            (user_id, google_event_id, title, description, start_time, end_time, location, synced, last_sync)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
        """
        
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get user ID
            cursor.execute(get_user_query, (line_user_id,))
            user = cursor.fetchone()
            if not user:
                raise ValueError(f"User not found: {line_user_id}")
            
            user_id = user["id"]
            
            # Parse datetime strings for MySQL
            start_dt = datetime.fromisoformat(start_time.replace('+09:00', ''))
            end_dt = datetime.fromisoformat(end_time.replace('+09:00', ''))
            
            # Ensure location is not None
            location_value = location if location is not None else ""
            
            # Insert event
            cursor.execute(
                insert_query,
                (user_id, google_event_id, title, description, start_dt, end_dt, location_value)
            )
            conn.commit()
            
            return cursor.lastrowid

    @staticmethod
    async def refresh_user_token(line_user_id: str, refresh_token: str) -> Optional[str]:
        """
        Refresh expired access token using refresh_token.
        
        Args:
            line_user_id: LINE user ID
            refresh_token: Refresh token
            
        Returns:
            New access_token if successful, None if failed
        """
        try:
            from services.google_service import get_google_client
            
            client = get_google_client()
            token_response = await client.refresh_access_token(refresh_token)
            new_access_token = token_response.get("access_token")
            expires_in = token_response.get("expires_in", 3600)
            
            if not new_access_token:
                raise ValueError("No access_token in refresh response")
            
            # Calculate new expiry time
            new_expiry = client.calculate_expiry_time(expires_in)
            
            # Update database
            update_query = """
                UPDATE users
                SET access_token = %s, token_expiry = %s
                WHERE line_user_id = %s
            """
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(update_query, (new_access_token, new_expiry, line_user_id))
                conn.commit()
            
            return new_access_token
        
        except Exception as e:
            print(f"Token refresh failed for {line_user_id}: {str(e)}")
            return None

    @staticmethod
    def is_token_expired(token_expiry) -> bool:
        """
        Check if token has expired.
        
        Args:
            token_expiry: Token expiry datetime from DB
            
        Returns:
            True if token is expired or expiring within 5 minutes
        """
        if not token_expiry:
            return True
        
        # Convert to datetime if it's a string
        if isinstance(token_expiry, str):
            token_expiry = datetime.fromisoformat(token_expiry)
        
        # Consider token expired if within 5 minutes
        buffer = 5 * 60  # 5 minutes in seconds
        expiry_with_buffer = token_expiry + timedelta(seconds=buffer)
        
        return datetime.now() >= expiry_with_buffer


    @staticmethod
    def check_event_exists(line_user_id: str, session_id: int) -> bool:
        """
        Check if an event has already been created for this user and session.
        Prevents duplicate event creation.
        
        Args:
            line_user_id: LINE user ID
            session_id: Poll session ID
            
        Returns:
            True if event already exists
        """
        query = """
            SELECT COUNT(*) as count
            FROM calendar_events ce
            JOIN users u ON ce.user_id = u.id
            WHERE u.line_user_id = %s
              AND ce.description LIKE %s
        """

        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            pattern = f"%session_id:{session_id}%"
            cursor.execute(query, (line_user_id, pattern))
            result = cursor.fetchone()
            return result["count"] > 0 if result else False


# Convenience function
async def create_event_for_session(
    session_id: int,
    event_title: str,
    date_label: str,
    start_time: str,
    end_time: str,
    location: Optional[str] = None,
    description_extra: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create calendar events for all connected users in a session.
    
    Args:
        session_id: Poll session ID
        event_title: Title for the calendar event
        date_label: Date label from poll response
        start_time: Start time string
        end_time: End time string
        location: Optional location (e.g., restaurant name)
        description_extra: Optional additional description
        
    Returns:
        Dict with success status and results per user
    """
    service = GoogleCalendarService()
    
    # Get all connected users
    connected_users = await service.get_all_connected_users(session_id)
    
    if not connected_users:
        return {
            "success": False,
            "message": "No users with Google Calendar connected",
            "created_events": []
        }
    
    results = []
    
    for user in connected_users:
        try:
            # Check and refresh token if expired
            access_token = user["access_token"]
            if service.is_token_expired(user["token_expiry"]):
                print(f"Token expired for {user['line_user_id']}, refreshing...")
                new_token = await service.refresh_user_token(user["line_user_id"], user["refresh_token"])
                if new_token:
                    access_token = new_token
                else:
                    raise Exception("Failed to refresh token")
            
            # Duplicate check skipped for now
            # Parse datetime
            start_dt = service._parse_datetime(date_label, start_time)
            end_dt = service._parse_datetime(date_label, end_time)
            
            # Create description with session ID for tracking
            description = f"session_id:{session_id}\n\n"
            if description_extra:
                description += description_extra
            
            # Create event
            event = await service.create_event(
                access_token=access_token,
                summary=event_title,
                start_datetime=start_dt,
                end_datetime=end_dt,
                description=description,
                location=location
            )
            
            # Save to database
            db_event_id = service.save_event_to_db(
                line_user_id=user["line_user_id"],
                google_event_id=event["id"],
                title=event_title,
                start_time=start_dt,
                end_time=end_dt,
                description=description,
                location=location
            )
            
            results.append({
                "line_user_id": user["line_user_id"],
                "display_name": user.get("display_name", "Unknown"),
                "success": True,
                "google_event_id": event["id"],
                "db_event_id": db_event_id,
                "event_link": event.get("htmlLink")
            })
        
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            results.append({
                "line_user_id": user["line_user_id"],
                "display_name": user.get("display_name", "Unknown"),
                "success": False,
                "error": error_detail
            })
    
    successful = [r for r in results if r["success"]]
    
    return {
        "success": len(successful) > 0,
        "message": f"Created {len(successful)}/{len(connected_users)} calendar events",
        "created_events": results,
        "total_users": len(connected_users),
        "successful_count": len(successful)
    }

