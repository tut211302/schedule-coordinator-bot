"""
FastAPI Backend for Google Calendar Integration
Main application entry point
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from line.webhook import line_router
from line.api import line_api_router

from services.hp_services import search_restaurants
from services.hp_services import get_location

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
app.include_router(line_api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )

@app.on_event("startup")
async def startup_event():
    print("--------------HOTPEPPER SERCH TEST----------------",flush=True)

    shops = search_restaurants(
            area_code = "Z011",
            genre_code = "G001",
            count = 10,
            min_price = 3000,
            max_price = 20000,
            location_name = "石川県金沢駅",
            )

    if shops:
        for shop in shops:
            print(f"- {shop.get('name')}  ({shop.get('genre').get('name')})",flush=True)
            print(f" {shop.get('genre').get('catch')}",flush=True)
            print(f" 予算:{shop.get('budget',{}).get('average')}",flush=True)
            print(f" 営業時間:{shop.get('open')}",flush=True)
            print(f" 定休日:{shop.get('close')}",flush=True)
            print(f" {shop.get('urls').get('pc')}",flush=True)
    else:
        print("No result",flush=True)

    print("--------------HOTPEPPER SERCH TEST END----------------",flush=True)

