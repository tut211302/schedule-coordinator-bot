"""
Vote completion handler - triggers restaurant suggestions when all members have voted.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_connection
from db.restaurant_conditions import get_aggregated_conditions
from api.hotpepper import search_restaurants, create_line_carousel_message
from line.reply import push_message, multicast_message


vote_completion_router = APIRouter()


class CheckCompletionRequest(BaseModel):
    session_id: int
    expected_voters: Optional[int] = None  # If None, check against linked users


class VoteSummary(BaseModel):
    session_id: int
    total_voters: int
    expected_voters: int
    is_complete: bool
    top_dates: List[Dict]


def get_session_voters(session_id: int) -> List[Dict]:
    """Get all users who have voted in this session."""
    query = """
        SELECT DISTINCT pr.line_user_id, lu.display_name
        FROM poll_responses pr
        LEFT JOIN line_users lu ON pr.line_user_id = lu.line_user_id
        WHERE pr.session_id = %s
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (session_id,))
        return cursor.fetchall()


def get_session_linked_users(session_id: int) -> List[Dict]:
    """Get all users linked to this session (from the initial group)."""
    query = """
        SELECT lu.line_user_id, lu.display_name
        FROM line_users lu
        WHERE lu.session_id = %s OR lu.session_id IS NULL
    """
    # For now, return all users who have voted (we'll improve this later)
    return get_session_voters(session_id)


def get_vote_results(session_id: int) -> List[Dict]:
    """Get aggregated vote results for a session."""
    query = """
        SELECT 
            pr.date_label,
            pr.start_time,
            pr.end_time,
            COUNT(*) as vote_count,
            GROUP_CONCAT(DISTINCT lu.display_name SEPARATOR ', ') as voters
        FROM poll_responses pr
        LEFT JOIN line_users lu ON pr.line_user_id = lu.line_user_id
        WHERE pr.session_id = %s
        GROUP BY pr.date_label, pr.start_time, pr.end_time
        ORDER BY vote_count DESC, pr.start_time ASC
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (session_id,))
        results = cursor.fetchall()
        
        # Convert datetime objects to strings
        for row in results:
            if row.get('start_time'):
                row['start_time'] = str(row['start_time'])
            if row.get('end_time'):
                row['end_time'] = str(row['end_time'])
        
        return results


def get_session_group_id(session_id: int) -> Optional[str]:
    """Get the group_id for a session to send messages to."""
    query = """
        SELECT group_id FROM poll_sessions WHERE id = %s
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (session_id,))
        row = cursor.fetchone()
        return row.get('group_id') if row else None


@vote_completion_router.get("/api/votes/check/{session_id}")
async def check_vote_completion(session_id: int, expected_voters: Optional[int] = None):
    """
    Check if all expected voters have completed voting.
    Returns vote summary and completion status.
    """
    voters = get_session_voters(session_id)
    total_voters = len(voters)
    
    # If expected_voters is not provided, we can't determine completion
    # For now, assume completion requires manual trigger or expected count
    if expected_voters is None:
        expected_voters = total_voters  # Assume current voters are all expected
    
    is_complete = total_voters >= expected_voters and total_voters > 0
    
    # Get top voted dates
    vote_results = get_vote_results(session_id)
    top_dates = vote_results[:5] if vote_results else []
    
    return {
        "session_id": session_id,
        "total_voters": total_voters,
        "expected_voters": expected_voters,
        "is_complete": is_complete,
        "voters": voters,
        "top_dates": top_dates
    }


@vote_completion_router.post("/api/votes/complete/{session_id}")
async def trigger_completion(session_id: int, expected_voters: Optional[int] = None):
    """
    Manually trigger the completion flow:
    1. Check if voting is complete
    2. Aggregate restaurant conditions
    3. Search Hotpepper API
    4. Send carousel to LINE group/users
    """
    # 1. Check vote completion
    completion_status = await check_vote_completion(session_id, expected_voters)
    
    # 2. Get aggregated restaurant conditions
    conditions = get_aggregated_conditions(session_id)
    
    # 3. Search restaurants based on aggregated conditions
    search_result = await search_restaurants(
        area=conditions.get("most_common_area"),
        genre_codes=conditions.get("most_common_genres", [])[:3],
        budget_code=conditions.get("most_common_budget"),
        count=10
    )
    
    shops = search_result.get("shops", [])
    
    if not shops:
        return {
            "success": False,
            "message": "条件に合うお店が見つかりませんでした",
            "vote_summary": completion_status,
            "conditions_used": conditions,
            "search_result": search_result
        }
    
    # 4. Create LINE carousel message
    carousel_message = create_line_carousel_message(shops, "🍻 おすすめのお店")
    
    # Create summary message
    top_date = completion_status["top_dates"][0] if completion_status["top_dates"] else None
    summary_text = f"🎉 投票が完了しました！\n\n"
    
    if top_date:
        summary_text += f"📅 最も人気の日程: {top_date['date_label']}\n"
        summary_text += f"   👥 {top_date['vote_count']}人が参加可能\n\n"
    
    if conditions.get("most_common_area"):
        summary_text += f"📍 エリア: {conditions['most_common_area']}\n"
    if conditions.get("most_common_genres"):
        summary_text += f"🍴 ジャンル: {', '.join(conditions['most_common_genres'][:2])}\n"
    if conditions.get("most_common_budget"):
        summary_text += f"💰 予算: {conditions['most_common_budget']}\n"
    
    summary_text += f"\n条件に合うお店を{len(shops)}件見つけました！"
    
    messages = [
        {"type": "text", "text": summary_text},
        carousel_message
    ]
    
    # 5. Send to LINE
    send_success = False
    
    # Try to send to group first
    group_id = get_session_group_id(session_id)
    if group_id:
        send_success = await push_message(group_id, messages)
    
    # If no group or group send failed, try multicast to individual users
    if not send_success:
        voter_ids = [v["line_user_id"] for v in completion_status["voters"] if v.get("line_user_id")]
        if voter_ids:
            send_success = await multicast_message(voter_ids, messages)
    
    return {
        "success": True,
        "message_sent": send_success,
        "vote_summary": completion_status,
        "conditions_used": conditions,
        "shops_found": len(shops),
        "carousel_message": carousel_message if not send_success else "Sent to LINE"
    }


@vote_completion_router.get("/api/votes/results/{session_id}")
async def get_session_results(session_id: int):
    """Get detailed voting results for a session."""
    voters = get_session_voters(session_id)
    vote_results = get_vote_results(session_id)
    conditions = get_aggregated_conditions(session_id)
    
    return {
        "session_id": session_id,
        "total_voters": len(voters),
        "voters": voters,
        "vote_results": vote_results,
        "restaurant_conditions": conditions
    }
