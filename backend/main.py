"""
FastAPI Backend for Google Calendar Integration
Main application entry point
"""

import base64
import hmac
import json
import os
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession
import hashlib
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Google Calendar Integration API",
    description="FastAPI backend for Google Calendar integration with React frontend",
    version="0.1.0"
)

# CORS設定
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE Messaging API 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
BOT_MENTION = os.getenv("BOT_MENTION", "").strip()  # 例: "@schedule-bot"
LINE_REPLY_ENDPOINT = "https://api.line.me/v2/bot/message/reply"


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """
    Verify LINE signature using channel secret.
    Docs: https://developers.line.biz/en/reference/messaging-api/#signature-validation
    """
    mac = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature)


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


async def handle_line_events(events: List[Dict[str, Any]]) -> None:
    """
    Stub handler for LINE events.
    - ここでAIルーター呼び出しやカレンダー処理を行う想定
    - 現状はログに残すのみ
    """
    for event in events:
        if should_handle_text(event, BOT_MENTION):
            message = event.get("message", {}).get("text", "")
            user_id = event.get("source", {}).get("userId")
            print(f"[LINE] text from {user_id}: {message}")
            reply_token = event.get("replyToken")
            if reply_token:
                await reply_text(reply_token, "メッセージを受け付けました。（AIルーターはこの後実装予定です）")
        else:
            print(f"[LINE] skipped event type={event.get('type')}")


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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Google Calendar Integration API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Google認証関連のエンドポイント（プレースホルダー）
@app.get("/api/auth/google/login")
async def google_login():
    """
    Google認証開始エンドポイント
    Googleの認証URLを返す
    """
    return JSONResponse({
        "authUrl": "https://accounts.google.com/o/oauth2/v2/auth?..."
    }, status_code=501)


@app.post("/api/auth/google/callback")
async def google_callback(code: str, state: str):
    """
    Google認証コールバックエンドポイント
    認証コードをアクセストークンと交換
    """
    return JSONResponse({
        "success": False,
        "message": "Backend implementation required"
    }, status_code=501)


@app.get("/api/user/calendar-status")
async def get_calendar_status():
    """
    ユーザーのカレンダー連携状態を取得
    """
    return JSONResponse({
        "isConnected": False,
        "email": None
    }, status_code=501)


@app.post("/api/auth/google/disconnect")
async def disconnect_calendar():
    """
    Googleカレンダーとの連携を解除
    """
    return JSONResponse({
        "success": False,
        "message": "Backend implementation required"
    }, status_code=501)


@app.post("/webhook/line")
async def line_webhook(request: Request):
    """
    LINE Messaging API webhook endpoint.
    - Signature verification with LINE_CHANNEL_SECRET
    - Filters to text messages; actual handling is delegated to handle_line_events
    """
    if not LINE_CHANNEL_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LINE_CHANNEL_SECRET is not configured",
        )

    signature = request.headers.get("x-line-signature", "")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Line-Signature header",
        )

    body = await request.body()
    if not verify_line_signature(body, signature, LINE_CHANNEL_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    events = payload.get("events", [])
    await handle_line_events(events)
    return {"success": True, "handledEvents": len(events)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
