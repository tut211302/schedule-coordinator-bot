"""
Restaurant conditions database operations.
Handles storing and retrieving user's restaurant search preferences.
"""

import json
from typing import Dict, List, Optional

from db import get_connection


def save_restaurant_conditions(
    line_user_id: str,
    session_id: Optional[int] = None,
    area: Optional[str] = None,
    genre_codes: Optional[List[str]] = None,
    budget_code: Optional[str] = None
) -> int:
    """
    Save or update restaurant search conditions for a user.
    Uses UPSERT (INSERT ... ON DUPLICATE KEY UPDATE) pattern.
    
    Args:
        line_user_id: LINE user ID
        session_id: Optional session ID
        area: Area/location string (e.g., "渋谷")
        genre_codes: List of Hotpepper genre codes (e.g., ["G001", "G004"])
        budget_code: Hotpepper budget code (e.g., "B002")
    
    Returns:
        ID of the inserted/updated record
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Convert genre_codes list to JSON string
        genre_codes_json = json.dumps(genre_codes) if genre_codes else None
        
        query = """
            INSERT INTO restaurant_conditions 
            (line_user_id, session_id, area, genre_codes, budget_code)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                area = VALUES(area),
                genre_codes = VALUES(genre_codes),
                budget_code = VALUES(budget_code),
                updated_at = CURRENT_TIMESTAMP
        """
        
        cursor.execute(query, (
            line_user_id,
            session_id,
            area,
            genre_codes_json,
            budget_code
        ))
        
        # Get the ID (either new insert or existing)
        if cursor.lastrowid:
            return cursor.lastrowid
        else:
            # If updated, get the existing ID
            cursor.execute(
                "SELECT id FROM restaurant_conditions WHERE line_user_id = %s AND session_id <=> %s",
                (line_user_id, session_id)
            )
            result = cursor.fetchone()
            return result[0] if result else 0


def get_restaurant_conditions(
    line_user_id: Optional[str] = None,
    session_id: Optional[int] = None
) -> List[Dict]:
    """
    Get restaurant conditions, optionally filtered by user or session.
    
    Args:
        line_user_id: Optional LINE user ID to filter by
        session_id: Optional session ID to filter by
    
    Returns:
        List of condition dictionaries
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM restaurant_conditions WHERE 1=1"
        params = []
        
        if line_user_id:
            query += " AND line_user_id = %s"
            params.append(line_user_id)
        
        if session_id is not None:
            query += " AND session_id = %s"
            params.append(session_id)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Parse JSON fields
        for row in results:
            if row.get('genre_codes'):
                try:
                    row['genre_codes'] = json.loads(row['genre_codes'])
                except (json.JSONDecodeError, TypeError):
                    row['genre_codes'] = []
        
        return results


def get_aggregated_conditions(session_id: int) -> Dict:
    """
    Get aggregated restaurant conditions for a session.
    Combines all users' preferences to find common ground.
    
    Args:
        session_id: Session ID to aggregate conditions for
    
    Returns:
        Dictionary with aggregated conditions:
        - areas: List of unique areas mentioned
        - genre_codes: Dict of genre codes with vote counts
        - budget_codes: Dict of budget codes with vote counts
        - most_common_area: Most frequently mentioned area
        - most_common_genres: List of most common genre codes
        - most_common_budget: Most common budget code
        - total_respondents: Number of users who submitted conditions
    """
    conditions = get_restaurant_conditions(session_id=session_id)
    
    if not conditions:
        return {
            "areas": [],
            "genre_codes": {},
            "budget_codes": {},
            "most_common_area": None,
            "most_common_genres": [],
            "most_common_budget": None,
            "total_respondents": 0
        }
    
    areas = []
    area_counts = {}
    genre_counts = {}
    budget_counts = {}
    
    for cond in conditions:
        # Collect and count areas
        if cond.get('area'):
            areas.append(cond['area'])
            area_counts[cond['area']] = area_counts.get(cond['area'], 0) + 1
        
        # Count genre codes
        genres = cond.get('genre_codes', [])
        if isinstance(genres, list):
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Count budget codes
        budget = cond.get('budget_code')
        if budget:
            budget_counts[budget] = budget_counts.get(budget, 0) + 1
    
    # Find most common values
    most_common_area = max(area_counts, key=area_counts.get) if area_counts else None
    most_common_genres = sorted(genre_counts, key=genre_counts.get, reverse=True)[:3] if genre_counts else []
    most_common_budget = max(budget_counts, key=budget_counts.get) if budget_counts else None
    
    return {
        "areas": list(set(areas)),
        "genre_codes": genre_counts,
        "budget_codes": budget_counts,
        "most_common_area": most_common_area,
        "most_common_genres": most_common_genres,
        "most_common_budget": most_common_budget,
        "total_respondents": len(conditions)
    }


def delete_user_conditions(line_user_id: str, session_id: Optional[int] = None) -> int:
    """
    Delete restaurant conditions for a user.
    
    Args:
        line_user_id: LINE user ID
        session_id: Optional session ID to filter by
    
    Returns:
        Number of deleted rows
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if session_id is not None:
            query = "DELETE FROM restaurant_conditions WHERE line_user_id = %s AND session_id = %s"
            cursor.execute(query, (line_user_id, session_id))
        else:
            query = "DELETE FROM restaurant_conditions WHERE line_user_id = %s"
            cursor.execute(query, (line_user_id,))
        
        return cursor.rowcount
