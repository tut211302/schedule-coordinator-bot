import json
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional

from db import get_connection


DEFAULT_SETTINGS = {
    "range_days": 14,
    "weekday_start": "19:00",
    "weekday_end": "21:00",
    "weekend_start": "18:00",
    "weekend_end": "20:00",
}


def _parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def _settings_json(settings: Optional[Dict]) -> str:
    merged = DEFAULT_SETTINGS.copy()
    if settings:
        merged.update(settings)
    return json.dumps(merged, ensure_ascii=True)


def _load_settings(raw_value) -> Dict:
    if not raw_value:
        return DEFAULT_SETTINGS.copy()
    if isinstance(raw_value, dict):
        merged = DEFAULT_SETTINGS.copy()
        merged.update(raw_value)
        return merged
    try:
        data = json.loads(raw_value)
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except (json.JSONDecodeError, TypeError):
        return DEFAULT_SETTINGS.copy()


def get_active_session(group_id: str) -> Optional[Dict]:
    query = """
        SELECT id, group_id, topic, state, created_by_line_user_id, settings_json
        FROM poll_sessions
        WHERE group_id = %s AND state != 'closed'
        ORDER BY id DESC
        LIMIT 1
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (group_id,))
        row = cursor.fetchone()
        if not row:
            return None
        row["settings"] = _load_settings(row.get("settings_json"))
        return row


def create_session(group_id: str, topic: str, created_by: str) -> int:
    query = """
        INSERT INTO poll_sessions (group_id, topic, state, created_by_line_user_id, settings_json)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            query,
            (group_id, topic, "pending_defaults", created_by, _settings_json(None)),
        )
        return cursor.lastrowid


def update_session_state(session_id: int, state: str) -> None:
    query = "UPDATE poll_sessions SET state=%s WHERE id=%s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (state, session_id))


def update_session_settings(session_id: int, settings: Dict) -> None:
    query = "UPDATE poll_sessions SET settings_json=%s WHERE id=%s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (_settings_json(settings), session_id))


def clear_options(session_id: int) -> None:
    query = "DELETE FROM poll_options WHERE session_id=%s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id,))


def add_option(
    session_id: int,
    start_time: datetime,
    end_time: datetime,
    label: str,
    created_by: str,
) -> int:
    query = """
        INSERT INTO poll_options (session_id, label, start_time, end_time, created_by_line_user_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id, label, start_time, end_time, created_by))
        return cursor.lastrowid


def delete_option(session_id: int, option_id: int) -> None:
    query = "DELETE FROM poll_options WHERE session_id=%s AND id=%s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id, option_id))


def list_options(session_id: int) -> List[Dict]:
    query = """
        SELECT o.id, o.label, o.start_time, o.end_time, COUNT(v.id) AS votes
        FROM poll_options o
        LEFT JOIN poll_votes v ON v.option_id = o.id
        WHERE o.session_id = %s
        GROUP BY o.id
        ORDER BY o.start_time
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (session_id,))
        return cursor.fetchall()


def record_vote(session_id: int, option_id: int, line_user_id: str) -> None:
    query = """
        INSERT INTO poll_votes (session_id, option_id, line_user_id)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE option_id=VALUES(option_id), updated_at=CURRENT_TIMESTAMP
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id, option_id, line_user_id))


def generate_default_options(session_id: int, settings: Dict) -> None:
    clear_options(session_id)
    start_date = date.today()
    range_days = int(settings.get("range_days", DEFAULT_SETTINGS["range_days"]))

    weekday_start = _parse_time(settings["weekday_start"])
    weekday_end = _parse_time(settings["weekday_end"])
    weekend_start = _parse_time(settings["weekend_start"])
    weekend_end = _parse_time(settings["weekend_end"])

    for offset in range(range_days):
        current_date = start_date + timedelta(days=offset)
        is_weekend = current_date.weekday() >= 5
        start_t = weekend_start if is_weekend else weekday_start
        end_t = weekend_end if is_weekend else weekday_end

        start_dt = datetime.combine(current_date, start_t)
        end_dt = datetime.combine(current_date, end_t)
        label = start_dt.strftime("%m/%d %H:%M") + "-" + end_dt.strftime("%H:%M")
        add_option(session_id, start_dt, end_dt, label, created_by="system")


def close_session(session_id: int) -> None:
    update_session_state(session_id, "closed")

