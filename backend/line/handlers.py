import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from line.config import BOT_MENTION, FRONTEND_BASE_URL, LIFF_ID
from line.reply import reply_text, reply_carousel
from db.poll import (
    close_session,
    create_session,
    delete_option,
    generate_default_options,
    get_active_session,
    list_options,
    record_vote,
    update_session_settings,
    update_session_state,
    add_option,
)

from services.hp_services import search_restaurants

DEFAULT_PROMPT = (
    "デフォルト候補を自動で作成しますか？\n"
    "期間: 今日〜14日 / 平日19:00-21:00 / 週末18:00-20:00\n"
    "OKなら「OK」、変更するなら「期間 10日」「時間帯 19:00-21:00」を送ってください。"
)

HELP_TEXT = (
    "使い方:\n"
    "開始 飲み会  -> セッション開始\n"
    "OK           -> デフォルト候補を作成\n"
    "候補 8/5 19:00-21:00 -> 候補追加\n"
    "1            -> 投票\n"
    "集計         -> 現在の票数\n"
    "確定 1       -> 確定\n"
    "削除 3       -> 候補削除"
)


def should_handle_text(event: Dict[str, Any], bot_mention: Optional[str] = None) -> bool:
    """Return True when the event is a text message we want to process."""
    if event.get("type") != "message":
        return False
    message = event.get("message", {})
    if message.get("type") != "text":
        return False
    text = message.get("text", "")

    # 個チャットは常に処理。グループ/複数人はメンションやプレフィックスで絞る
    source_type = event.get("source", {}).get("type")
    if source_type == "user":
        return True

    # メンション情報があれば優先
    mention = message.get("mention", {})
    if mention and mention.get("mentionees"):
        return True

    if bot_mention:
        return bot_mention in text
    return False


def _strip_mention(event: Dict[str, Any], text: str, bot_mention: str) -> str:
    message = event.get("message", {})
    mention = message.get("mention", {})
    mentionees = mention.get("mentionees", [])
    if mentionees:
        cleaned = text
        for item in sorted(mentionees, key=lambda m: m.get("index", 0), reverse=True):
            index = item.get("index", 0)
            length = item.get("length", 0)
            if length:
                cleaned = cleaned[:index] + cleaned[index + length :]
        return cleaned.strip()
    if bot_mention and bot_mention in text:
        return text.replace(bot_mention, "").strip()
    return text.strip()


def _conversation_id(event: Dict[str, Any]) -> str:
    source = event.get("source", {})
    return source.get("groupId") or source.get("roomId") or source.get("userId") or "unknown"


def _parse_time_range(text: str) -> Optional[Tuple[str, str]]:
    match = re.search(r"(\d{1,2}):(\d{2})\s*[-~]\s*(\d{1,2}):(\d{2})", text)
    if not match:
        return None
    start = f"{int(match.group(1)):02d}:{match.group(2)}"
    end = f"{int(match.group(3)):02d}:{match.group(4)}"
    return start, end


def _parse_candidate(text: str) -> Optional[Tuple[datetime, datetime, str]]:
    date_match = re.search(r"(\d{1,4})[/-](\d{1,2})[/-](\d{1,2})", text)
    time_match = re.search(r"(\d{1,2}):(\d{2})\s*[-~]\s*(\d{1,2}):(\d{2})", text)
    if not time_match:
        return None

    now = datetime.now()
    if date_match:
        year = int(date_match.group(1))
        month = int(date_match.group(2))
        day = int(date_match.group(3))
    else:
        short_match = re.search(r"(\d{1,2})[/-](\d{1,2})", text)
        if not short_match:
            return None
        year = now.year
        month = int(short_match.group(1))
        day = int(short_match.group(2))

    start_hour, start_min = int(time_match.group(1)), int(time_match.group(2))
    end_hour, end_min = int(time_match.group(3)), int(time_match.group(4))
    start_dt = datetime(year, month, day, start_hour, start_min)
    end_dt = datetime(year, month, day, end_hour, end_min)
    label = start_dt.strftime("%m/%d %H:%M") + "-" + end_dt.strftime("%H:%M")
    return start_dt, end_dt, label


def _format_options(options: List[Dict[str, Any]]) -> str:
    if not options:
        return "候補がまだありません。"
    lines = []
    for idx, option in enumerate(options, start=1):
        start = option["start_time"].strftime("%m/%d %H:%M")
        end = option["end_time"].strftime("%H:%M")
        votes = option.get("votes", 0)
        lines.append(f"{idx}. {start}-{end} ({votes}票)")
    return "\n".join(lines)


def _poll_link(session_id: int) -> str:
    if LIFF_ID:
        return f"https://liff.line.me/{LIFF_ID}?sessionId={session_id}"
    base = FRONTEND_BASE_URL.rstrip("/")
    return f"{base}/poll/{session_id}"


def _parse_range_days(text: str) -> Optional[int]:
    match = re.search(r"(\d+)\s*日", text)
    if not match:
        return None
    return int(match.group(1))


async def handle_line_events(events: List[Dict[str, Any]]) -> None:
    """
    Stub handler for LINE events.
    - ここでAIルーター呼び出しやカレンダー処理を行う想定
    - 現状はログに残すのみ
    """
    for event in events:
        if should_handle_text(event, BOT_MENTION):
            raw_message = event.get("message", {}).get("text", "")
            user_id = event.get("source", {}).get("userId", "")
            message = _strip_mention(event, raw_message, BOT_MENTION)
            print(f"[LINE] text from {user_id}: {message}")
            reply_token = event.get("replyToken")
            response = await _route_message(event, message)
            if reply_token and response:
                if isinstance(response, str):
                    await reply_text(reply_token, response)
                else:
                    await reply_carousel(
                            reply_token,
                            response.get("alt_txt","おすすめのお店"),
                            response.get("columns",[]),
                            )
        else:
            print(f"[LINE] skipped event type={event.get('type')}")


async def _route_message(event: Dict[str, Any], message: str) -> Optional[Union[str,Dict[str, Any]]]:
    group_id = _conversation_id(event)
    user_id = event.get("source", {}).get("userId", "")
    session = get_active_session(group_id)

    if message in {"ヘルプ", "help", "?"}:
        return HELP_TEXT

    if session and session["state"] == "pending_defaults":
        if message in {"OK", "ok", "はい", "開始", "デフォルト"}:
            generate_default_options(session["id"], session["settings"])
            update_session_state(session["id"], "voting")
            link = _poll_link(session["id"])
            return f"投票ページ: {link}"

        if message.startswith("期間"):
            days = _parse_range_days(message)
            if not days:
                return "期間の指定が読み取れませんでした。（例: 期間 10日）"
            settings = session["settings"]
            settings["range_days"] = days
            update_session_settings(session["id"], settings)
            return f"期間を{days}日に更新しました。\nOKで候補を作成します。"

        if message.startswith("時間帯"):
            time_range = _parse_time_range(message)
            if not time_range:
                return "時間帯の指定が読み取れませんでした。（例: 時間帯 19:00-21:00）"
            start_time, end_time = time_range
            settings = session["settings"]
            settings["weekday_start"] = start_time
            settings["weekday_end"] = end_time
            settings["weekend_start"] = start_time
            settings["weekend_end"] = end_time
            update_session_settings(session["id"], settings)
            return f"時間帯を{start_time}-{end_time}に更新しました。\nOKで候補を作成します。"

    if message.startswith("開始"):
        if session:
            options = list_options(session["id"])
            return "すでに進行中の投票があります。\n" + _format_options(options)
        topic = message.replace("開始", "", 1).strip() or "予定調整"
        create_session(group_id, topic, user_id)
        return f"「{topic}」の投票を開始します。\n{DEFAULT_PROMPT}"

    if message.startswith("候補"):
        if not session:
            return "先に「開始 <タイトル>」で投票を始めてください。"
        parsed = _parse_candidate(message)
        if not parsed:
            return "候補の形式が読み取れませんでした。（例: 候補 8/5 19:00-21:00）"
        start_dt, end_dt, label = parsed
        add_option(session["id"], start_dt, end_dt, label, user_id)
        options = list_options(session["id"])
        return "候補を追加しました。\n" + _format_options(options)

    if message.startswith("削除"):
        if not session:
            return "削除する投票が見つかりません。"
        match = re.search(r"(\d+)", message)
        if not match:
            return "削除する候補番号を指定してください。（例: 削除 2）"
        options = list_options(session["id"])
        index = int(match.group(1))
        if index < 1 or index > len(options):
            return "指定の候補番号が見つかりません。"
        delete_option(session["id"], options[index - 1]["id"])
        options = list_options(session["id"])
        return "候補を削除しました。\n" + _format_options(options)

    if message in {"候補一覧", "一覧", "リスト", "集計"}:
        if not session:
            return "進行中の投票がありません。"
        options = list_options(session["id"])
        return _format_options(options)

    if message.startswith("確定"):
        if not session:
            return "進行中の投票がありません。"
        match = re.search(r"(\d+)", message)
        if not match:
            return "確定する候補番号を指定してください。（例: 確定 1）"
        options = list_options(session["id"])
        index = int(match.group(1))
        if index < 1 or index > len(options):
            return "指定の候補番号が見つかりません。"
        chosen = options[index - 1]
        close_session(session["id"])
        start = chosen["start_time"].strftime("%m/%d %H:%M")
        end = chosen["end_time"].strftime("%H:%M")
        return f"候補を確定しました。{start}-{end}"

    if re.fullmatch(r"\d+", message):
        if not session:
            return "進行中の投票がありません。"
        options = list_options(session["id"])
        index = int(message)
        if index < 1 or index > len(options):
            return "指定の候補番号が見つかりません。"
        record_vote(session["id"], options[index - 1]["id"], user_id)
        options = list_options(session["id"])
        return "投票を受け付けました。\n" + _format_options(options)

    return None
