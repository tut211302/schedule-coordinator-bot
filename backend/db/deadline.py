"""
Deadline database operations.
Handles storing and retrieving voting deadlines for sessions.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from db import get_connection

# 日本時間 (JST = UTC+9)
JST = timezone(timedelta(hours=9))

# 開発用: 2分（本番は 24 * 60 = 1440分 = 24時間に変更）
DEFAULT_DEADLINE_MINUTES = 2

# 開発モード: True = サイトを開いた時に期限切れなら新しい期限を作成
# 本番モード: False = LINE Botが作成した期限をそのまま使用
# ※ 一度期限が切れたらリロードしても投票不可にするため、falseに設定
DEV_MODE_RESET_EXPIRED = os.getenv("DEV_MODE_RESET_EXPIRED", "false").lower() == "true"


def now_jst() -> datetime:
    """Get current time in JST."""
    return datetime.now(JST)


def create_deadline(
    session_id: int,
    group_id: Optional[str] = None,
    deadline_minutes: Optional[int] = None
) -> Dict:
    """
    Create a new deadline for a session.
    
    Args:
        session_id: Poll session ID
        group_id: LINE group ID (optional)
        deadline_minutes: Minutes from now until deadline (default: DEFAULT_DEADLINE_MINUTES)
    
    Returns:
        Dictionary with deadline info
    """
    if deadline_minutes is None:
        deadline_minutes = DEFAULT_DEADLINE_MINUTES
    
    # JSTで期限を計算（タイムゾーン情報なしでDBに保存）
    deadline = now_jst() + timedelta(minutes=deadline_minutes)
    deadline_naive = deadline.replace(tzinfo=None)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            INSERT INTO adjustment_events (session_id, group_id, deadline)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                group_id = VALUES(group_id),
                deadline = VALUES(deadline),
                updated_at = CURRENT_TIMESTAMP
        """
        
        cursor.execute(query, (session_id, group_id, deadline_naive))
        
        return {
            "session_id": session_id,
            "group_id": group_id,
            "deadline": deadline_naive.isoformat(),
            "deadline_minutes": deadline_minutes
        }


def get_deadline(session_id: int) -> Optional[Dict]:
    """
    Get deadline information for a session.
    
    Args:
        session_id: Poll session ID
    
    Returns:
        Dictionary with deadline info or None if not found
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT id, session_id, group_id, deadline, created_at, updated_at
            FROM adjustment_events
            WHERE session_id = %s
        """
        
        cursor.execute(query, (session_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        deadline = row['deadline']
        # JSTで現在時刻を取得（タイムゾーン情報なし）
        now = now_jst().replace(tzinfo=None)
        
        return {
            "id": row['id'],
            "session_id": row['session_id'],
            "group_id": row['group_id'],
            "deadline": deadline.isoformat() if deadline else None,
            "is_expired": deadline < now if deadline else False,
            "remaining_seconds": max(0, int((deadline - now).total_seconds())) if deadline else 0,
            "created_at": row['created_at'].isoformat() if row['created_at'] else None
        }


def check_deadline_expired(session_id: int) -> bool:
    """
    Check if the deadline for a session has expired.
    
    Args:
        session_id: Poll session ID
    
    Returns:
        True if expired or no deadline exists, False otherwise
    """
    deadline_info = get_deadline(session_id)
    
    if not deadline_info:
        # No deadline set - allow voting (for backward compatibility)
        return False
    
    return deadline_info['is_expired']


def get_or_create_deadline(
    session_id: int,
    group_id: Optional[str] = None,
    deadline_minutes: Optional[int] = None,
    reset_if_expired: Optional[bool] = None
) -> Dict:
    """
    Get existing deadline or create a new one if it doesn't exist.
    
    Args:
        session_id: Poll session ID
        group_id: LINE group ID (optional)
        deadline_minutes: Minutes from now until deadline (default: DEFAULT_DEADLINE_MINUTES)
        reset_if_expired: If True, create new deadline when existing one is expired.
                         If None, uses DEV_MODE_RESET_EXPIRED setting.
                         開発モード: True（サイトを開くたびに新しい期限）
                         本番モード: False（LINE Botが作成した期限を使用）
    
    Returns:
        Dictionary with deadline info
    """
    # reset_if_expired が指定されていない場合は環境変数の設定を使用
    if reset_if_expired is None:
        reset_if_expired = DEV_MODE_RESET_EXPIRED
    
    existing = get_deadline(session_id)
    
    if existing:
        # 開発モード: 期限切れの場合は新しい期限を作成
        if reset_if_expired and existing.get('is_expired'):
            return create_deadline(session_id, group_id, deadline_minutes)
        return existing
    
    return create_deadline(session_id, group_id, deadline_minutes)


def delete_deadline(session_id: int) -> bool:
    """
    Delete a deadline for a session.
    
    Args:
        session_id: Poll session ID
    
    Returns:
        True if deleted, False if not found
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        query = "DELETE FROM adjustment_events WHERE session_id = %s"
        cursor.execute(query, (session_id,))
        
        return cursor.rowcount > 0
