"""
Poll responses database operations.
Handles storing and retrieving user vote responses.
"""

from datetime import datetime
from typing import Dict, List, Optional

from db import get_connection


def save_poll_responses(
    line_user_id: str,
    votes: List[Dict],
    session_id: Optional[int] = None
) -> int:
    """
    Save poll responses for a user.
    Performs a "replace" operation: deletes existing responses for the user
    before inserting new ones.
    
    Args:
        line_user_id: LINE user ID
        votes: List of vote objects with 'date', 'start_time', 'end_time', 'is_late'
        session_id: Optional session ID to associate votes with
    
    Returns:
        Number of responses saved
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Delete existing responses for this user (and session if specified)
        if session_id:
            delete_query = """
                DELETE FROM poll_responses 
                WHERE line_user_id = %s AND session_id = %s
            """
            cursor.execute(delete_query, (line_user_id, session_id))
        else:
            delete_query = """
                DELETE FROM poll_responses 
                WHERE line_user_id = %s AND session_id IS NULL
            """
            cursor.execute(delete_query, (line_user_id,))
        
        # Insert new responses
        insert_query = """
            INSERT INTO poll_responses 
            (line_user_id, session_id, selected_date, start_time, end_time, is_late)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        for vote in votes:
            selected_date = vote.get('date', '')
            start_time = vote.get('start_time')
            end_time = vote.get('end_time')
            is_late = vote.get('is_late', False)
            
            # Parse datetime strings if provided
            if isinstance(start_time, str) and start_time:
                try:
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except ValueError:
                    start_time = None
            
            if isinstance(end_time, str) and end_time:
                try:
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                except ValueError:
                    end_time = None
            
            cursor.execute(insert_query, (
                line_user_id,
                session_id,
                selected_date,
                start_time,
                end_time,
                is_late
            ))
        
        return len(votes)


def get_poll_responses(
    line_user_id: Optional[str] = None,
    session_id: Optional[int] = None
) -> List[Dict]:
    """
    Get poll responses, optionally filtered by user or session.
    
    Args:
        line_user_id: Optional LINE user ID to filter by
        session_id: Optional session ID to filter by
    
    Returns:
        List of response dictionaries
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM poll_responses WHERE 1=1"
        params = []
        
        if line_user_id:
            query += " AND line_user_id = %s"
            params.append(line_user_id)
        
        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()


def get_response_summary(session_id: Optional[int] = None) -> Dict:
    """
    Get a summary of poll responses.
    
    Args:
        session_id: Optional session ID to filter by
    
    Returns:
        Dictionary with total_voters and vote_counts
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Count unique voters
        voters_query = """
            SELECT COUNT(DISTINCT line_user_id) as total_voters
            FROM poll_responses
        """
        voters_params = []
        
        if session_id:
            voters_query += " WHERE session_id = %s"
            voters_params.append(session_id)
        
        cursor.execute(voters_query, voters_params)
        result = cursor.fetchone()
        total_voters = result['total_voters'] if result else 0
        
        # Count votes per date
        counts_query = """
            SELECT selected_date, COUNT(*) as vote_count
            FROM poll_responses
        """
        counts_params = []
        
        if session_id:
            counts_query += " WHERE session_id = %s"
            counts_params.append(session_id)
        
        counts_query += " GROUP BY selected_date ORDER BY selected_date"
        
        cursor.execute(counts_query, counts_params)
        rows = cursor.fetchall()
        
        vote_counts = {row['selected_date']: row['vote_count'] for row in rows}
        
        # Get voters by date
        voters_by_date_query = """
            SELECT pr.selected_date, pr.line_user_id, lu.display_name
            FROM poll_responses pr
            LEFT JOIN line_users lu ON pr.line_user_id = lu.line_user_id
        """
        if session_id:
            voters_by_date_query += " WHERE pr.session_id = %s"
        
        cursor.execute(voters_by_date_query, counts_params)
        voter_rows = cursor.fetchall()
        
        voters_by_option = {}
        for row in voter_rows:
            date_key = row['selected_date']
            if date_key not in voters_by_option:
                voters_by_option[date_key] = []
            
            voter_name = row.get('display_name') or f"ユーザー{row['line_user_id'][-4:]}"
            voters_by_option[date_key].append({
                'user_id': row['line_user_id'],
                'display_name': voter_name
            })
        
        return {
            'total_voters': total_voters,
            'vote_counts': vote_counts,
            'voters_by_option': voters_by_option
        }


def get_top_voted_slot(session_id: int) -> Optional[Dict]:
    """
    Get the most-voted slot for a session.
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT selected_date, start_time, end_time, COUNT(*) AS vote_count
            FROM poll_responses
            WHERE session_id = %s
            GROUP BY selected_date, start_time, end_time
            ORDER BY vote_count DESC, start_time ASC
            LIMIT 1
        """
        cursor.execute(query, (session_id,))
        return cursor.fetchone()


def delete_user_responses(line_user_id: str, session_id: Optional[int] = None) -> int:
    """
    Delete all responses for a user.
    
    Args:
        line_user_id: LINE user ID
        session_id: Optional session ID to filter by
    
    Returns:
        Number of deleted rows
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if session_id:
            query = "DELETE FROM poll_responses WHERE line_user_id = %s AND session_id = %s"
            cursor.execute(query, (line_user_id, session_id))
        else:
            query = "DELETE FROM poll_responses WHERE line_user_id = %s"
            cursor.execute(query, (line_user_id,))
        
        return cursor.rowcount
