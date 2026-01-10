"""
FastAPI LINE Bot Webhook エンドポイント
このファイルを backend/main.py に統合してください
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
from datetime import datetime

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureException, LineBotApiException
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FollowEvent,
    UnfollowEvent,
    PostbackEvent,
)

from database import get_db, SessionLocal
from models.line_channel import LineChannel
from models.rich_menu import RichMenu
from models.user_rich_menu import UserRichMenu
from sqlalchemy.orm import Session

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LINE Bot API の初期化
def get_line_bot_api(db: Session = Depends(get_db)):
    """LINE Bot API を取得"""
    channel_id = os.getenv('LINE_CHANNEL_ID')
    access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    
    if not channel_id or not access_token:
        raise HTTPException(status_code=400, detail="LINE credentials not configured")
    
    return LineBotApi(access_token)


def get_webhook_parser(db: Session = Depends(get_db)):
    """Webhook Parser を取得"""
    channel_id = os.getenv('LINE_CHANNEL_ID')
    channel_secret = os.getenv('LINE_CHANNEL_SECRET')
    
    if not channel_id or not channel_secret:
        raise HTTPException(status_code=400, detail="LINE credentials not configured")
    
    return WebhookParser(channel_secret)


# ===============================
# Webhook ハンドラー
# ===============================

async def handle_follow_event(
    user_id: str,
    reply_token: str,
    line_bot_api: LineBotApi,
    db: Session
):
    """フォローイベント処理"""
    logger.info(f"📌 Follow event: user_id={user_id}")
    
    # デフォルトメニューを取得
    channel_id = os.getenv('LINE_CHANNEL_ID')
    channel = db.query(LineChannel).filter(
        LineChannel.channel_id == channel_id,
        LineChannel.is_active == 1
    ).first()
    
    if channel:
        default_menu = db.query(RichMenu).filter(
            RichMenu.channel_id == channel.id,
            RichMenu.is_default == 1,
            RichMenu.is_active == 1
        ).first()
        
        if default_menu:
            # 既存のメニューを無効化
            db.query(UserRichMenu).filter(
                UserRichMenu.user_id == user_id,
                UserRichMenu.is_active == 1
            ).update({"is_active": 0})
            
            # デフォルトメニューを設定
            user_menu = UserRichMenu(
                user_id=user_id,
                line_user_id=user_id,
                rich_menu_id=default_menu.id,
                is_active=1
            )
            db.add(user_menu)
            db.commit()
            logger.info(f"  ✅ Default menu set: {default_menu.display_name}")
    
    # ウェルカムメッセージ
    try:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text="🎉 Schedule Coordinator Botへようこそ！\n"
                     "このBotでは以下の機能が利用できます：\n\n"
                     "📅 予定の確認・登録\n"
                     "🔗 Googleカレンダー連携\n"
                     "⚙️ 設定管理\n\n"
                     "メニューのボタンからお選びください"
            )
        )
        logger.info(f"  ✅ Welcome message sent")
    except LineBotApiException as e:
        logger.error(f"  ❌ Error sending message: {e}")


async def handle_unfollow_event(user_id: str, db: Session):
    """ブロックイベント処理"""
    logger.info(f"📌 Unfollow event: user_id={user_id}")
    
    # ユーザーのメニューを無効化
    db.query(UserRichMenu).filter(
        UserRichMenu.user_id == user_id
    ).update({"is_active": 0})
    db.commit()
    logger.info(f"  ✅ User menus deactivated")


async def handle_text_message(
    user_id: str,
    text: str,
    reply_token: str,
    line_bot_api: LineBotApi,
    db: Session
):
    """テキストメッセージ処理"""
    logger.info(f"💬 Text message from {user_id}: {text}")
    
    # ユーザーのメニューを取得
    user_menu = db.query(UserRichMenu).filter(
        UserRichMenu.user_id == user_id,
        UserRichMenu.is_active == 1
    ).first()
    
    # メッセージに応じた処理
    response_text = None
    
    if text in ["予定を確認", "予定確認"]:
        response_text = (
            "📅 予定を確認します\n\n"
            "[ここに今後の予定が表示されます]\n\n"
            "より詳細を見るにはWebサイトをご利用ください"
        )
    elif text in ["予定を登録", "予定登録"]:
        response_text = (
            "➕ 新しい予定を登録します\n\n"
            "[ここに登録フォームが表示されます]\n\n"
            "Webサイトからの登録がおすすめです"
        )
    elif text in ["カレンダー連携", "連携"]:
        response_text = (
            "🔗 Googleカレンダーと連携します\n\n"
            "[ここに連携画面が表示されます]\n\n"
            "Webサイトの「設定」からご利用ください"
        )
    elif text in ["設定", "セッティング"]:
        response_text = (
            "⚙️ 設定画面\n\n"
            "以下から選択してください：\n"
            "1️⃣ 通知設定\n"
            "2️⃣ メニューカスタマイズ\n"
            "3️⃣ プロフィール設定"
        )
    elif text in ["ヘルプ", "help"]:
        response_text = (
            "ℹ️ Schedule Coordinator Bot ヘルプ\n\n"
            "使用可能なコマンド：\n"
            "• 予定を確認\n"
            "• 予定を登録\n"
            "• カレンダー連携\n"
            "• 設定\n"
            "• ステータス"
        )
    elif text in ["ステータス", "status"]:
        menu_name = user_menu.rich_menu.display_name if user_menu else "未設定"
        response_text = (
            f"📊 ステータス\n\n"
            f"ユーザーID: {user_id}\n"
            f"メニュー: {menu_name}\n"
            f"登録日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        response_text = (
            f"ご入力ありがとうございます\n\n"
            f"入力内容: {text}\n\n"
            f"「ヘルプ」でコマンド一覧を確認してください"
        )
    
    # レスポンス送信
    try:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=response_text)
        )
        logger.info(f"  ✅ Response sent")
    except LineBotApiException as e:
        logger.error(f"  ❌ Error sending message: {e}")


async def handle_postback_event(
    user_id: str,
    postback_data: str,
    reply_token: str,
    line_bot_api: LineBotApi,
    db: Session
):
    """ポストバックイベント処理（メニューボタン）"""
    logger.info(f"🔘 Postback event from {user_id}: {postback_data}")
    
    # ポストバックデータを解析（例：action=menu_confirm&menu_id=123）
    params = {}
    for param in postback_data.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key] = value
    
    response_text = f"ポストバック処理: {postback_data}"
    
    try:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=response_text)
        )
        logger.info(f"  ✅ Postback response sent")
    except LineBotApiException as e:
        logger.error(f"  ❌ Error sending message: {e}")


# ===============================
# FastAPI エンドポイント
# ===============================

def create_line_webhook_routes(app: FastAPI):
    """LINE Webhook ルートを追加"""
    
    @app.post("/webhook/line")
    async def handle_line_webhook(
        request: Request,
        db: Session = Depends(get_db)
    ):
        """
        LINE Webhook エンドポイント
        
        LINE Developers Console で以下のURLを設定してください：
        https://<your-domain>/webhook/line
        """
        
        # ヘッダーとボディを取得
        signature = request.headers.get('X-Line-Signature', '')
        body = await request.body()
        
        logger.info(f"📨 Webhook received (signature present: {bool(signature)})")
        
        # Parser を取得
        try:
            parser = get_webhook_parser(db)
        except HTTPException as e:
            logger.error(f"❌ Parser initialization failed: {e.detail}")
            return JSONResponse({"status": "error", "message": e.detail}, status_code=400)
        
        # イベントをパース
        try:
            events = parser.parse(body.decode('utf-8'), signature)
            logger.info(f"✅ Events parsed: {len(events)} events")
        except InvalidSignatureException:
            logger.error("❌ Invalid signature")
            return JSONResponse({"status": "error", "message": "Invalid signature"}, status_code=400)
        except Exception as e:
            logger.error(f"❌ Parse error: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=400)
        
        # LINE Bot API を取得
        try:
            line_bot_api = get_line_bot_api(db)
        except HTTPException as e:
            logger.error(f"❌ LINE Bot API initialization failed: {e.detail}")
            return JSONResponse({"status": "error", "message": e.detail}, status_code=400)
        
        # イベントを処理
        for event in events:
            try:
                if isinstance(event, FollowEvent):
                    await handle_follow_event(
                        event.source.user_id,
                        event.reply_token,
                        line_bot_api,
                        db
                    )
                elif isinstance(event, UnfollowEvent):
                    await handle_unfollow_event(event.source.user_id, db)
                elif isinstance(event, MessageEvent):
                    if isinstance(event.message, TextMessage):
                        await handle_text_message(
                            event.source.user_id,
                            event.message.text,
                            event.reply_token,
                            line_bot_api,
                            db
                        )
                elif isinstance(event, PostbackEvent):
                    await handle_postback_event(
                        event.source.user_id,
                        event.postback.data,
                        event.reply_token,
                        line_bot_api,
                        db
                    )
            except Exception as e:
                logger.error(f"❌ Error handling event: {e}", exc_info=True)
        
        return JSONResponse({"status": "ok"})


def create_line_management_routes(app: FastAPI):
    """LINE チャネル管理 API ルートを追加"""
    
    @app.get("/api/line/channels")
    async def list_line_channels(db: Session = Depends(get_db)):
        """LINE チャネル一覧を取得"""
        try:
            channels = db.query(LineChannel).all()
            return {
                "status": "success",
                "channels": [ch.to_dict() for ch in channels]
            }
        except Exception as e:
            logger.error(f"❌ Error listing channels: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/line/channels/{channel_id}/menus")
    async def list_channel_menus(channel_id: str, db: Session = Depends(get_db)):
        """チャネルのリッチメニュー一覧を取得"""
        try:
            channel = db.query(LineChannel).filter(
                LineChannel.channel_id == channel_id
            ).first()
            
            if not channel:
                raise HTTPException(status_code=404, detail="Channel not found")
            
            menus = db.query(RichMenu).filter(
                RichMenu.channel_id == channel.id
            ).all()
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "menus": [m.to_dict() for m in menus]
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error listing menus: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/line/users/{user_id}/menu")
    async def get_user_menu(user_id: str, db: Session = Depends(get_db)):
        """ユーザーの現在のメニュー情報を取得"""
        try:
            user_menu = db.query(UserRichMenu).filter(
                UserRichMenu.user_id == user_id,
                UserRichMenu.is_active == 1
            ).first()
            
            if not user_menu:
                return {
                    "status": "success",
                    "user_id": user_id,
                    "menu": None
                }
            
            return {
                "status": "success",
                "user_id": user_id,
                "menu": user_menu.to_dict(include_rich_menu=True)
            }
        except Exception as e:
            logger.error(f"❌ Error getting user menu: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/line/users/{user_id}/menu/{menu_id}")
    async def set_user_menu(
        user_id: str,
        menu_id: int,
        db: Session = Depends(get_db)
    ):
        """ユーザーにメニューを設定"""
        try:
            # メニューを確認
            menu = db.query(RichMenu).filter(
                RichMenu.id == menu_id,
                RichMenu.is_active == 1
            ).first()
            
            if not menu:
                raise HTTPException(status_code=404, detail="Menu not found")
            
            # 既存のアクティブなメニューを無効化
            db.query(UserRichMenu).filter(
                UserRichMenu.user_id == user_id,
                UserRichMenu.is_active == 1
            ).update({"is_active": 0})
            
            # 新しいメニューを設定
            user_menu = UserRichMenu(
                user_id=user_id,
                rich_menu_id=menu_id,
                is_active=1
            )
            db.add(user_menu)
            db.commit()
            db.refresh(user_menu)
            
            logger.info(f"✅ Menu {menu_id} set for user {user_id}")
            
            return {
                "status": "success",
                "user_id": user_id,
                "menu": user_menu.to_dict(include_rich_menu=True)
            }
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error setting user menu: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# ===============================
# 統合関数
# ===============================

def setup_line_bot_routes(app: FastAPI):
    """すべてのLINE Bot ルートをセットアップ"""
    create_line_webhook_routes(app)
    create_line_management_routes(app)
    logger.info("✅ LINE Bot routes configured")


# ===============================
# backend/main.py への統合例
# ===============================

"""
以下のコードを backend/main.py に追加してください：

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_line_webhook import setup_line_bot_routes
from database import init_db

app = FastAPI(title="Schedule Coordinator Bot")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE Bot ルートをセットアップ
setup_line_bot_routes(app)

@app.on_event("startup")
async def startup():
    init_db()
    logger.info("✅ Database initialized")

@app.on_event("shutdown")
async def shutdown():
    logger.info("✅ Application shutting down")

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
