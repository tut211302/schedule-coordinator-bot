from typing import Dict, Optional

from db.restaurant_conditions import get_conditions, upsert_conditions


def update_conditions(group_id: str, session_id: Optional[int], conditions: Dict) -> str:
    upsert_conditions(group_id, session_id, conditions)
    summary = _format_conditions(conditions)
    return f"条件を更新しました。\n{summary}\n探すなら「探して」と送ってください。"


def summarize_conditions(group_id: str) -> str:
    current = get_conditions(group_id)
    if not current:
        return "条件がまだ設定されていません。"
    return _format_conditions(current)


def _format_conditions(conditions: Dict) -> str:
    parts = []
    if conditions.get("area"):
        parts.append(f"エリア: {conditions['area']}")
    if conditions.get("genre"):
        parts.append(f"ジャンル: {conditions['genre']}")
    if conditions.get("budget_min") or conditions.get("budget_max"):
        min_v = conditions.get("budget_min")
        max_v = conditions.get("budget_max")
        if min_v and max_v:
            parts.append(f"予算: {min_v}-{max_v}円")
        elif max_v:
            parts.append(f"予算: 〜{max_v}円")
        elif min_v:
            parts.append(f"予算: {min_v}円〜")
    if conditions.get("party_size"):
        parts.append(f"人数: {conditions['party_size']}人")
    if conditions.get("date"):
        parts.append(f"日付: {conditions['date']}")
    if conditions.get("start_time") or conditions.get("end_time"):
        start_time = conditions.get("start_time")
        end_time = conditions.get("end_time")
        if start_time and end_time:
            parts.append(f"時間: {start_time}-{end_time}")
        elif start_time:
            parts.append(f"開始: {start_time}")
        elif end_time:
            parts.append(f"終了: {end_time}")
    if conditions.get("time_slot"):
        parts.append(f"時間帯: {conditions['time_slot']}")
    if not parts:
        return "条件: なし"
    return "条件: " + " / ".join(parts)
