from typing import Optional

from db.poll import (
    create_session,
    generate_default_options,
    get_active_session,
    update_session_state,
)

DEFAULT_PROMPT = (
    "デフォルト候補を自動で作成しますか？\n"
    "期間: 今日〜14日 / 平日19:00-21:00 / 週末17:00-20:00\n"
    "OKなら「OK」、変更するなら「期間 10日」「時間帯 19:00-21:00」を送ってください。"
)


def start_poll_flow(group_id: str, user_id: str, topic: str) -> str:
    session = get_active_session(group_id)
    if session:
        return "すでに進行中の投票があります。"
    create_session(group_id, topic, user_id)
    return f"「{topic}」の投票を開始します。\n{DEFAULT_PROMPT}"


def confirm_default_candidates(group_id: str) -> Optional[tuple[str, int]]:
    session = get_active_session(group_id)
    if not session or session["state"] != "pending_defaults":
        return None
    generate_default_options(session["id"], session["settings"])
    update_session_state(session["id"], "voting")
    return "候補を作成しました。投票ページのリンクを確認してください。", session["id"]


def confirm_poll(group_id: str, option_index: int) -> Optional[str]:
    session = get_active_session(group_id)
    if not session:
        return None
    from db.poll import list_options, close_session

    options = list_options(session["id"])
    if option_index < 1 or option_index > len(options):
        return "指定の候補番号が見つかりません。"
    chosen = options[option_index - 1]
    close_session(session["id"])
    start = chosen["start_time"].strftime("%m/%d %H:%M")
    end = chosen["end_time"].strftime("%H:%M")
    return f"候補を確定しました。{start}-{end}\nお店を探しますか？"
