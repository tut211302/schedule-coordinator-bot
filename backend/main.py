"""
FastAPI Backend for Google Calendar Integration
Main application entry point
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from line.webhook import line_router
from line.api import line_api_router
from routers import user, line_auth, google_auth

# Load environment variables
load_dotenv()

app = FastAPI(
    title="らくらく飲み会幹事Bot Backend API",
    description="LINE上で飲み会の企画から日程調整、お店選びまでを一元的にサポートするBotのバックエンドAPIです。",
    version="0.1.0",
)

# CORS設定
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

frontend_base_url = os.getenv("FRONTEND_BASE_URL")
if frontend_base_url:
    ALLOWED_ORIGINS.append(frontend_base_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "らくらく飲み会幹事Bot Backend API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# ========== API ルーター登録 ==========

# ユーザー管理 API (F008)
app.include_router(user.router, prefix="/users", tags=["ユーザー管理"])

# LINE認証 API (F011) - 新実装（ユーザー登録・プロフィール取得統合）
app.include_router(line_auth.router, prefix="/line", tags=["LINE認証"])

# Google認証 API (F012)
app.include_router(google_auth.router, prefix="/google", tags=["Google認証"])

# 既存の LINE Webhook ルーター（/webhook/line で既存の投票機能など）
app.include_router(line_router, tags=["LINE (既存)"])
app.include_router(line_api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
