from typing import Dict, List, Union
from aiohttp import ClientSession

from line.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_REPLY_ENDPOINT


LINE_PUSH_ENDPOINT = "https://api.line.me/v2/bot/message/push"
LINE_MULTICAST_ENDPOINT = "https://api.line.me/v2/bot/message/multicast"


async def reply_text(reply_token: str, text: str) -> None:
    """Send a simple text reply via Messaging API."""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("[LINE] LINE_CHANNEL_ACCESS_TOKEN is not configured; skip reply")
        return

    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text[:2000]}],
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


async def reply_messages(reply_token: str, messages: List[Dict]) -> None:
    """Send multiple messages via Reply API."""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("[LINE] LINE_CHANNEL_ACCESS_TOKEN is not configured; skip reply")
        return

    payload = {
        "replyToken": reply_token,
        "messages": messages[:5],  # Max 5 messages per reply
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


async def push_message(to: str, messages: Union[Dict, List[Dict]]) -> bool:
    """Send a push message to a user or group."""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("[LINE] LINE_CHANNEL_ACCESS_TOKEN is not configured; skip push")
        return False

    if isinstance(messages, dict):
        messages = [messages]

    payload = {
        "to": to,
        "messages": messages[:5],  # Max 5 messages per push
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    
    async with ClientSession() as session:
        async with session.post(LINE_PUSH_ENDPOINT, headers=headers, json=payload) as resp:
            if resp.status >= 400:
                body = await resp.text()
                print(f"[LINE] push failed status={resp.status} body={body}")
                return False
            return True


async def multicast_message(user_ids: List[str], messages: Union[Dict, List[Dict]]) -> bool:
    """Send a multicast message to multiple users."""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("[LINE] LINE_CHANNEL_ACCESS_TOKEN is not configured; skip multicast")
        return False

    if isinstance(messages, dict):
        messages = [messages]

    # LINE multicast limit: 500 users per request
    if len(user_ids) > 500:
        user_ids = user_ids[:500]

    payload = {
        "to": user_ids,
        "messages": messages[:5],  # Max 5 messages per multicast
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    
    async with ClientSession() as session:
        async with session.post(LINE_MULTICAST_ENDPOINT, headers=headers, json=payload) as resp:
            if resp.status >= 400:
                body = await resp.text()
                print(f"[LINE] multicast failed status={resp.status} body={body}")
                return False
            return True
