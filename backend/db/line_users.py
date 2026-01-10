from typing import Optional

from db import get_connection


def upsert_line_user(
    line_user_id: str,
    display_name: Optional[str] = None,
    picture_url: Optional[str] = None,
) -> None:
    query = """
        INSERT INTO line_users (line_user_id, display_name, picture_url)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            display_name = VALUES(display_name),
            picture_url = VALUES(picture_url),
            updated_at = CURRENT_TIMESTAMP
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (line_user_id, display_name, picture_url))
