"""
FastAPI Backend for Google Calendar Integration
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from line.webhook import line_router

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


app.include_router(line_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
