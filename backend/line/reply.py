from aiohttp import ClientSession

from line.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_REPLY_ENDPOINT


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

