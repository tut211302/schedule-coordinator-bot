"""
Restaurant vote database operations.
Stores per-user shop selections for a session.
"""

from typing import Dict, List, Optional

from db import get_connection


def save_restaurant_vote(
    line_user_id: str,
    session_id: int,
    shop_id: str,
    shop_name: Optional[str] = None,
) -> int:
    """
    Save or update restaurant vote for a user in a session.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            INSERT INTO restaurant_votes
            (session_id, line_user_id, shop_id, shop_name)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                shop_id = VALUES(shop_id),
                shop_name = VALUES(shop_name),
                updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(query, (session_id, line_user_id, shop_id, shop_name))
        if cursor.lastrowid:
            return cursor.lastrowid
        cursor.execute(
            "SELECT id FROM restaurant_votes WHERE session_id = %s AND line_user_id = %s",
            (session_id, line_user_id),
        )
        row = cursor.fetchone()
        return row[0] if row else 0


def get_restaurant_votes(session_id: int) -> List[Dict]:
    """Get all restaurant votes for a session."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT shop_id, shop_name, COUNT(*) AS vote_count
            FROM restaurant_votes
            WHERE session_id = %s
            GROUP BY shop_id, shop_name
            ORDER BY vote_count DESC, shop_name ASC
            """,
            (session_id,),
        )
        return cursor.fetchall()


def get_top_restaurant(session_id: int) -> Optional[Dict]:
    """Get top-voted restaurant for a session."""
    votes = get_restaurant_votes(session_id)
    return votes[0] if votes else None
