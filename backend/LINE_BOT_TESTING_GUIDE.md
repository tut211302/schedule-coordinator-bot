"""
LINE Botの実装とLINEアプリテストガイド
実際のLINEアプリでテストするための完全なセットアップ手順
"""

# LINE Bot実装・テストガイド

このガイドでは、実装したDBモデルを使用して、実際のLINEアプリでテストするまでの手順を説明します。

## 📋 目次

1. [前提条件](#前提条件)
2. [LINE Developers Consoleの設定](#line-developers-consoleの設定)
3. [ローカル環境のセットアップ](#ローカル環境のセットアップ)
4. [FastAPIエンドポイント実装](#fastapiエンドポイント実装)
5. [Webhook トンネリング](#webhook-トンネリング)
6. [LINEアプリでのテスト](#lineアプリでのテスト)
7. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

以下のファイルが完成していることを確認してください：

- ✅ [./backend/models/line_channel.py](./backend/models/line_channel.py)
- ✅ [./backend/models/rich_menu.py](./backend/models/rich_menu.py)
- ✅ [./backend/models/user_rich_menu.py](./backend/models/user_rich_menu.py)
- ✅ [./backend/database.py](./backend/database.py)
- ✅ [./db/init/02-line-rich-menu-schema.sql](./db/init/02-line-rich-menu-schema.sql)

---

## LINE Developers Consoleの設定

### Step 1: LINEビジネスアカウントの作成

1. [LINE Business Center](https://business.line.biz) にアクセス
2. ビジネスアカウントを作成 または ログイン
3. [LINE Developers](https://developers.line.biz/ja/) にアクセス

### Step 2: チャネルの作成

1. [LINE Developers Console](https://developers.line.biz/console/) を開く
2. 「プロバイダー」を作成 (初回のみ)
3. 「チャネル」→「Messaging API」を選択
4. チャネル名、説明などを入力

### Step 3: 認証情報の取得

チャネルが作成されたら、以下の情報を取得して記録：

```
チャネルID: [Channel ID]
チャネルシークレット: [Channel Secret]
チャネルアクセストークン: [Channel Access Token]
```

### Step 4: Bot基本設定

1. チャネル設定画面の「Bot」セクション
2. 「Webhook設定」→「Webhookの利用」を「有効」に変更
3. Webhook URL には後で設定 (Step 5: Webhook トンネリング で実施)

---

## ローカル環境のセットアップ

### Step 1: 環境変数の設定

[backend/.env](./backend/.env.example) を参考に、`.env` ファイルを作成：

```env
# LINE Messaging API Settings
LINE_CHANNEL_ID=your_channel_id_here
LINE_CHANNEL_SECRET=your_channel_secret_here
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_NAME=Schedule Coordinator Bot

# Database Settings
DATABASE_URL=mysql+mysqlconnector://devuser:devpass123@localhost:3306/calendar_db

# API Settings
API_BASE_URL=http://localhost:8000
WEBHOOK_PATH=/webhook/line
```

### Step 2: 依存関係の確認・インストール

```bash
# Dockerコンテナ内で
cd /app
poetry install

# または個別にインストール
poetry add linebot pydantic-settings
```

### Step 3: データベースの確認

```bash
# テストスクリプトで確認
python test_models.py

# 期待結果: 5/5 テスト合格
```

---

## FastAPIエンドポイント実装

### Step 1: LINE Bot用エンドポイントの追加

[backend/main.py](./backend/main.py) に以下のコードを追加します：

```python
# backend/main.py の先頭に追加
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureException, LineBotApiException
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FollowEvent,
    UnfollowEvent,
)
from models.line_channel import LineChannel
from models.rich_menu import RichMenu
from models.user_rich_menu import UserRichMenu
from database import get_db, SessionLocal

# LINE Messaging API初期化
def get_line_bot_api():
    """LINE Bot API インスタンス取得"""
    channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    return LineBotApi(channel_access_token)

def get_line_bot_parser():
    """LINE Webhook パーサー取得"""
    channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
    return WebhookParser(channel_secret)

# ========================================
# Webhook エンドポイント
# ========================================

@app.post("/webhook/line")
async def handle_line_webhook(request: Request):
    """
    LINE Webhookイベントハンドラー
    
    LINEプラットフォームから送られてくるイベント (メッセージ、フォロー等) を処理
    """
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    
    # 署名検証
    parser = get_line_bot_parser()
    try:
        events = parser.parse(body.decode('utf-8'), signature)
    except InvalidSignatureException:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # イベント処理
    line_bot_api = get_line_bot_api()
    for event in events:
        try:
            if isinstance(event, FollowEvent):
                await handle_follow(event, line_bot_api)
            elif isinstance(event, UnfollowEvent):
                await handle_unfollow(event, line_bot_api)
            elif isinstance(event, MessageEvent):
                if isinstance(event.message, TextMessage):
                    await handle_text_message(event, line_bot_api)
        except Exception as e:
            print(f"Error handling event: {e}")
    
    return JSONResponse({"status": "ok"})

# ========================================
# イベントハンドラー
# ========================================

async def handle_follow(event: FollowEvent, line_bot_api: LineBotApi):
    """ユーザーがBotをフォローした時の処理"""
    user_id = event.source.user_id
    
    # ユーザーデータベースに保存 (例: users テーブル)
    print(f"User followed: {user_id}")
    
    # ウェルカムメッセージを送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Schedule Coordinator Botへようこそ！\n予定管理をサポートします。")
    )

async def handle_unfollow(event: UnfollowEvent, line_bot_api: LineBotApi):
    """ユーザーがBotをブロックした時の処理"""
    user_id = event.source.user_id
    print(f"User unfollowed: {user_id}")

async def handle_text_message(event: MessageEvent, line_bot_api: LineBotApi):
    """テキストメッセージの処理"""
    user_id = event.source.user_id
    text = event.message.text
    
    # ユーザーに設定されているリッチメニューを取得
    db = SessionLocal()
    try:
        user_menu = db.query(UserRichMenu).filter(
            UserRichMenu.user_id == user_id,
            UserRichMenu.is_active == 1
        ).first()
        
        # メッセージに応じた処理
        if text == "予定を確認":
            response = "📅 予定を確認します..."
        elif text == "予定を登録":
            response = "➕ 新しい予定を登録します..."
        elif text == "カレンダー連携":
            response = "🔗 Googleカレンダーと連携します..."
        elif text == "設定":
            response = "⚙️ 設定画面です..."
        else:
            response = f"ご入力ありがとうございます: {text}"
        
        # レスポンスを送信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
    finally:
        db.close()

# ========================================
# 管理用API
# ========================================

@app.post("/api/line/channels")
async def create_line_channel(
    channel_id: str,
    channel_name: str,
    channel_access_token: str,
    channel_secret: str,
    webhook_url: str = None,
    db: Session = Depends(get_db)
):
    """
    LINEチャネル設定を登録
    
    LINE Developers Consoleから取得した情報をデータベースに保存
    """
    # 既存チャネルを確認
    existing = db.query(LineChannel).filter(
        LineChannel.channel_id == channel_id
    ).first()
    
    if existing:
        # 既存の場合は更新
        existing.channel_name = channel_name
        existing.channel_access_token = channel_access_token
        existing.channel_secret = channel_secret
        if webhook_url:
            existing.webhook_url = webhook_url
        db.commit()
        db.refresh(existing)
        return {"status": "updated", "channel": existing.to_dict()}
    else:
        # 新規作成
        channel = LineChannel(
            channel_id=channel_id,
            channel_name=channel_name,
            channel_access_token=channel_access_token,
            channel_secret=channel_secret,
            webhook_url=webhook_url,
            is_active=1
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)
        return {"status": "created", "channel": channel.to_dict()}

@app.get("/api/line/channels")
async def list_line_channels(db: Session = Depends(get_db)):
    """
    登録されたLINEチャネルを一覧取得
    """
    channels = db.query(LineChannel).filter(
        LineChannel.is_active == 1
    ).all()
    return [ch.to_dict() for ch in channels]

@app.get("/api/line/user/{user_id}/menu")
async def get_user_menu(user_id: str, db: Session = Depends(get_db)):
    """
    ユーザーに設定されているリッチメニューを取得
    """
    user_menu = db.query(UserRichMenu).filter(
        UserRichMenu.user_id == user_id,
        UserRichMenu.is_active == 1
    ).first()
    
    if not user_menu:
        return {"status": "not_found", "user_id": user_id}
    
    return {
        "status": "found",
        "user_id": user_id,
        "menu": user_menu.to_dict(include_rich_menu=True)
    }

@app.post("/api/line/user/{user_id}/menu/{menu_id}")
async def set_user_menu(
    user_id: str,
    menu_id: int,
    line_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    ユーザーにリッチメニューを設定
    """
    # メニューが存在するか確認
    menu = db.query(RichMenu).filter(RichMenu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    # 既存のアクティブなメニューを非アクティブ化
    db.query(UserRichMenu).filter(
        UserRichMenu.user_id == user_id,
        UserRichMenu.is_active == 1
    ).update({"is_active": 0})
    
    # 新しいメニューを設定
    user_menu = UserRichMenu(
        user_id=user_id,
        line_user_id=line_user_id,
        rich_menu_id=menu_id,
        is_active=1
    )
    db.add(user_menu)
    db.commit()
    db.refresh(user_menu)
    
    return {
        "status": "success",
        "message": f"Menu {menu_id} set for user {user_id}",
        "user_menu": user_menu.to_dict()
    }

# ========================================
# Webhook URL確認用エンドポイント
# ========================================

@app.get("/webhook/line")
async def webhook_get():
    """
    GETリクエスト用エンドポイント
    LINE Developers Console での Webhook URL 確認用
    """
    return {
        "status": "ok",
        "message": "LINE Webhook is active",
        "endpoint": "/webhook/line"
    }
```

---

## Webhook トンネリング

ローカル開発環境をインターネット経由でLINEプラットフォームに公開します。

### Option 1: ngrok を使用 (推奨)

```bash
# ngrok をダウンロード
# https://ngrok.com/download

# ngrok を起動 (別ターミナル)
./ngrok http 8000

# 出力例:
# Forwarding    https://abc123def456-123.ngrok.io -> http://localhost:8000

# Webhook URL を設定
# https://abc123def456-123.ngrok.io/webhook/line
```

### Option 2: Docker ネットワークを使用

```bash
# docker-compose.yml で設定
# (ホストマシンのIPアドレスを使用)
```

### Step 1: Webhook URLを LINE Developers Console に設定

1. チャネル設定画面にアクセス
2. 「Webhook設定」セクションを開く
3. Webhook URL を入力:
   ```
   https://abc123def456-123.ngrok.io/webhook/line
   ```
4. 「Verify」ボタンで確認

---

## LINEアプリでのテスト

### Step 1: テストアカウントの準備

1. LINE Developers Console の「チャネル設定」
2. 「Bot」セクション下部に QR コードがある
3. LINEアプリでスキャンして Bot をフォロー

### Step 2: メッセージ送信テスト

LINEアプリから以下のテキストを送信して動作確認：

```
メッセージ例:
- "予定を確認"
- "予定を登録"
- "カレンダー連携"
- "設定"
- その他のテキスト
```

### Step 3: ボットからの応答確認

各メッセージに対してボットが適切に応答することを確認：

| 入力 | 期待される応答 |
|-----|--------------|
| 予定を確認 | 📅 予定を確認します... |
| 予定を登録 | ➕ 新しい予定を登録します... |
| カレンダー連携 | 🔗 Googleカレンダーと連携します... |
| 設定 | ⚙️ 設定画面です... |
| その他 | ご入力ありがとうございます: [入力テキスト] |

### Step 4: データベース確認

```bash
# MySQL に接続
docker exec -it schedule-coordinator-db mysql -u devuser -p calendar_db

# ユーザー・メニュー紐付けを確認
SELECT * FROM user_rich_menus;

# ユーザーメッセージログを確認 (実装済みの場合)
SELECT * FROM message_logs;
```

---

## 高度なテスト: リッチメニューの設定

### Step 1: リッチメニューを作成 (LINE Developers Console)

1. チャネル設定 → 「リッチメニュー」
2. 「リッチメニューを作成」をクリック
3. メニュー構造を設計
4. 「公開」をクリック
5. リッチメニューID を取得

### Step 2: データベースに登録

```python
from database import SessionLocal
from models.line_channel import LineChannel
from models.rich_menu import RichMenu

db = SessionLocal()

# チャネルを取得
channel = db.query(LineChannel).first()

# リッチメニュー定義
menu_json = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "Main Menu",
    "chatBarText": "メニュー",
    "areas": [
        {
            "bounds": {"x": 0, "y": 0, "width": 1250, "height": 843},
            "action": {"type": "message", "text": "予定を確認"}
        },
        {
            "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 843},
            "action": {"type": "message", "text": "予定を登録"}
        },
        {
            "bounds": {"x": 0, "y": 843, "width": 1250, "height": 843},
            "action": {"type": "message", "text": "カレンダー連携"}
        },
        {
            "bounds": {"x": 1250, "y": 843, "width": 1250, "height": 843},
            "action": {"type": "message", "text": "設定"}
        }
    ]
}

# リッチメニューを作成
menu = RichMenu(
    rich_menu_line_id="richmenu-xxxxxxxxxxxx",  # LINE Developers Console から取得
    channel_id=channel.id,
    name="main_menu",
    display_name="メインメニュー",
    image_url="https://your-server.com/images/menu.png",
    rich_menu_json_definition=menu_json,
    is_active=1,
    is_default=1
)
db.add(menu)
db.commit()
db.refresh(menu)

print(f"Rich menu created: {menu.id}")

db.close()
```

### Step 3: ユーザーにメニューを設定

```python
# API経由で設定
import requests

response = requests.post(
    "http://localhost:8000/api/line/user/U1234567890abcdef/menu/1",
    json={"line_user_id": "U1234567890abcdef"}
)
print(response.json())
```

---

## トラブルシューティング

### 問題1: Webhook が受信されない

**症状**: LINEアプリからメッセージを送っても応答がない

**解決方法**:
1. ngrok が起動しているか確認
2. Webhook URL が正しいか確認
3. LINE Developers Console で「Verify」が成功しているか確認
4. ファイアウォール設定を確認
5. バックエンドアプリケーションが起動しているか確認

```bash
# ログを確認
docker logs schedule-coordinator-backend

# Webhook URL をテスト
curl https://abc123def456-123.ngrok.io/webhook/line
# 期待結果: {"status":"ok","message":"LINE Webhook is active",...}
```

### 問題2: 署名検証エラー

**症状**: `InvalidSignatureException` エラー

**解決方法**:
1. チャネルシークレットが正しいか確認
2. `.env` ファイルの `LINE_CHANNEL_SECRET` を確認
3. チャネルシークレットを再生成してみる

### 問題3: データベース接続エラー

**症状**: `DBConnectionError` または `DatabaseError`

**解決方法**:
1. MySQL コンテナが起動しているか確認
2. `.env` ファイルの `DATABASE_URL` を確認
3. テストスクリプトを実行: `python test_models.py`

### 問題4: チャネルアクセストークンエラー

**症状**: `LineBotApiException` 401 Unauthorized

**解決方法**:
1. チャネルアクセストークンが正しいか確認
2. トークンの有効期限を確認
3. 必要に応じてトークンを再生成

---

## ログ・デバッグ情報

### ログレベルの設定

```python
# backend/main.py に追加
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Webhook ハンドラーで使用
logger.info(f"Received event from user: {user_id}")
logger.debug(f"Event details: {event}")
```

### Webhook イベントのログ出力

```python
@app.post("/webhook/line")
async def handle_line_webhook(request: Request):
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    
    logger.debug(f"Webhook signature: {signature}")
    logger.debug(f"Webhook body: {body.decode('utf-8')}")
    
    # ... 以下同じ ...
```

---

## まとめ

このガイドに従うことで、以下が実現できます：

✅ LINE Developers Console での設定完了  
✅ ローカル開発環境の構築  
✅ FastAPI Webhook エンドポイント実装  
✅ ngrok によるトンネリング  
✅ LINEアプリでの実動作テスト  
✅ リッチメニューの統合  

---

## 次のステップ

1. **ユーザー管理機能の拡張**
   - ユーザー認証
   - プロフィール管理

2. **メッセージ処理の高度化**
   - ステート管理
   - 会話フロー実装

3. **カレンダー連携**
   - Google Calendar API 統合
   - スケジュール自動同期

4. **アナリティクス**
   - ユーザー行動トラッキング
   - メニュー使用統計

---

**作成日**: 2026年1月9日  
**バージョン**: 1.0  
**最終更新**: 2026年1月9日
