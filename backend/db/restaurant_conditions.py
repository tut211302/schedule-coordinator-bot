from typing import Dict, Optional

from db import get_connection


def upsert_conditions(
    group_id: str,
    session_id: Optional[int],
    conditions: Dict,
) -> None:
    query = """
        INSERT INTO restaurant_conditions (
            group_id,
            session_id,
            area,
            budget_min,
            budget_max,
            party_size,
            genre,
            date_value,
            start_time,
            end_time,
            time_slot
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            area = VALUES(area),
            budget_min = VALUES(budget_min),
            budget_max = VALUES(budget_max),
            party_size = VALUES(party_size),
            genre = VALUES(genre),
            date_value = VALUES(date_value),
            start_time = VALUES(start_time),
            end_time = VALUES(end_time),
            time_slot = VALUES(time_slot),
            updated_at = CURRENT_TIMESTAMP
    """
    values = (
        group_id,
        session_id,
        conditions.get("area"),
        conditions.get("budget_min"),
        conditions.get("budget_max"),
        conditions.get("party_size"),
        conditions.get("genre"),
        conditions.get("date"),
        conditions.get("start_time"),
        conditions.get("end_time"),
        conditions.get("time"),
    )
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values)


def get_conditions(group_id: str) -> Optional[Dict]:
    query = """
        SELECT area, budget_min, budget_max, party_size, genre, date_value, start_time, end_time, time_slot
        FROM restaurant_conditions
        WHERE group_id = %s
        ORDER BY updated_at DESC
        LIMIT 1
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (group_id,))
        return cursor.fetchone()
