from typing import Any, Dict, List

from aiohttp import ClientSession

from line.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_REPLY_ENDPOINT


async def reply_messages(reply_token: str, messages: List[Dict[str, Any]]) -> None:
    """Send arbitrary message payloads via Messaging API."""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("[LINE] LINE_CHANNEL_ACCESS_TOKEN is not configured; skip reply")
        return
    if not messages:
        return

    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    async with ClientSession() as session:
        async with session.post(LINE_REPLY_ENDPOINT, headers=headers, json=payload) as resp:
            if resp.status >= 400:
                body = await resp.text()
                print(f"[LINE] reply failed status={resp.status} body={body}")


async def reply_text(reply_token: str, text: str) -> None:
    """Send a simple text reply via Messaging API."""
    message = {"type": "text", "text": text[:2000]}
    await reply_messages(reply_token, [message])


async def reply_carousel(
    reply_token: str, alt_text: str, columns: List[Dict[str, Any]]
) -> None:
    """Send a carousel template message."""
    message = {
        "type": "template",
        "altText": alt_text[:400],
        "template": {"type": "carousel", "columns": columns},
    }
    await reply_messages(reply_token, [message])
