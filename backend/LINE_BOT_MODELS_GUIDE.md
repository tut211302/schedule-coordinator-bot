# LINE Bot チャネル設定とリッチメニュー定義 - 実装ガイド

## 📋 目次

1. [概要](#概要)
2. [ファイル構成](#ファイル構成)
3. [モデル設計](#モデル設計)
4. [データベーススキーマ](#データベーススキーマ)
5. [セットアップ手順](#セットアップ手順)
6. [使用方法](#使用方法)
7. [テスト手順](#テスト手順)
8. [API統合例](#api統合例)

---

## 概要

このドキュメントでは、LINE Botのチャネル設定情報とリッチメニュー定義を管理するためのデータベースモデルとスキーマの実装について説明します。

### 実装の目的

- **LINE Bot設定の一元管理**: チャネルアクセストークン、シークレットなどの認証情報を安全に管理
- **動的なリッチメニュー管理**: リッチメニューの定義をデータベースで管理し、動的な切り替えを実現
- **ユーザーごとのカスタマイズ**: ユーザーの状態や行動に応じて異なるメニューを表示

### 主な機能

✅ LINE Botチャネル設定の管理  
✅ リッチメニュー定義のJSON形式での保存  
✅ ユーザーとリッチメニューの紐付け管理  
✅ 期限付きメニューの設定  
✅ デフォルトメニューの指定

---

## ファイル構成

```
backend/
├── models/
│   ├── __init__.py                  # モデルパッケージ初期化
│   ├── line_channel.py              # LINEチャネル設定モデル
│   ├── rich_menu.py                 # リッチメニュー定義モデル
│   └── user_rich_menu.py            # ユーザー・メニュー紐付けモデル
├── database.py                      # データベース設定・接続管理
├── test_models.py                   # モデルテストスクリプト
├── main.py                          # FastAPIアプリケーション
└── pyproject.toml                   # Python依存関係定義

db/
└── init/
    ├── 01-schema.sql                # 既存スキーマ（ユーザー、イベント等）
    └── 02-line-rich-menu-schema.sql # LINE Bot関連スキーマ（新規）
```

---

## モデル設計

### 1. LineChannel モデル

LINE Botのチャネル設定情報を管理します。

**主要フィールド:**

| フィールド名 | 型 | 説明 |
|------------|-----|------|
| id | Integer | 内部ID（主キー） |
| channel_id | String(255) | LINEチャネルID（一意） |
| channel_name | String(255) | チャネル表示名 |
| channel_access_token | String(512) | アクセストークン |
| channel_secret | String(255) | チャネルシークレット |
| webhook_url | String(512) | Webhook URL |
| is_active | Integer | 有効/無効状態 |

**リレーション:**
- `rich_menus`: このチャネルに紐づくリッチメニュー（1対多）

**使用例:**

```python
from models.line_channel import LineChannel

# チャネル作成
channel = LineChannel(
    channel_id="1234567890",
    channel_name="My Schedule Bot",
    channel_access_token="your_token_here",
    channel_secret="your_secret_here",
    webhook_url="https://your-domain.com/webhook",
    is_active=1
)
db.add(channel)
db.commit()

# チャネル取得
channel = db.query(LineChannel).filter(
    LineChannel.channel_id == "1234567890"
).first()

# 辞書に変換（APIレスポンス用）
channel_dict = channel.to_dict()
```

---

### 2. RichMenu モデル

リッチメニューの定義情報を管理します。

**主要フィールド:**

| フィールド名 | 型 | 説明 |
|------------|-----|------|
| id | Integer | 内部ID（主キー） |
| rich_menu_line_id | String(255) | LINEリッチメニューID（一意） |
| channel_id | Integer | 紐づくチャネルID（外部キー） |
| name | String(255) | 識別名 |
| display_name | String(255) | 表示名 |
| image_url | String(512) | メニュー画像URL |
| rich_menu_json_definition | JSON | メニュー定義（JSON） |
| is_active | Integer | 有効/無効状態 |
| is_default | Integer | デフォルトメニュー |

**JSONフィールドの構造:**

```json
{
  "size": {
    "width": 2500,
    "height": 1686
  },
  "selected": true,
  "name": "Main Menu",
  "chatBarText": "メニュー",
  "areas": [
    {
      "bounds": {
        "x": 0,
        "y": 0,
        "width": 1250,
        "height": 843
      },
      "action": {
        "type": "message",
        "text": "予定を確認"
      }
    }
  ]
}
```

**リレーション:**
- `channel`: 紐づくLINEチャネル（多対1）
- `user_rich_menus`: このメニューを使用しているユーザー（1対多）

**使用例:**

```python
from models.rich_menu import RichMenu

# リッチメニュー作成
menu_json = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "Main Menu",
    "chatBarText": "メニュー",
    "areas": [...]
}

menu = RichMenu(
    rich_menu_line_id="richmenu-abc123",
    channel_id=1,
    name="main_menu",
    display_name="メインメニュー",
    image_url="https://example.com/menu.png",
    rich_menu_json_definition=menu_json,
    is_active=1,
    is_default=1
)
db.add(menu)
db.commit()

# メニュー取得とヘルパーメソッド使用
menu = db.query(RichMenu).first()
areas = menu.get_menu_areas()
size = menu.get_menu_size()
```

---

### 3. UserRichMenu モデル

ユーザーとリッチメニューの紐付けを管理します。

**主要フィールド:**

| フィールド名 | 型 | 説明 |
|------------|-----|------|
| id | Integer | 内部ID（主キー） |
| user_id | String(255) | アプリケーションのユーザーID |
| line_user_id | String(255) | LINEユーザーID |
| rich_menu_id | Integer | 紐づくリッチメニューID（外部キー） |
| is_active | Integer | 有効/無効状態 |
| set_at | DateTime | 設定日時 |
| expires_at | DateTime | 有効期限（NULL=無期限） |

**リレーション:**
- `rich_menu`: 紐づくリッチメニュー（多対1）

**制約:**
- `UNIQUE(user_id, is_active)`: 1ユーザーにつき1つの有効なメニューのみ

**使用例:**

```python
from models.user_rich_menu import UserRichMenu
from datetime import datetime, timedelta

# ユーザーにメニューを紐付け
user_menu = UserRichMenu(
    user_id="user123",
    line_user_id="U1234567890",
    rich_menu_id=1,
    is_active=1,
    expires_at=datetime.utcnow() + timedelta(days=30)
)
db.add(user_menu)
db.commit()

# ユーザーのメニュー取得
user_menu = db.query(UserRichMenu).filter(
    UserRichMenu.user_id == "user123",
    UserRichMenu.is_active == 1
).first()

# 期限チェック
if user_menu.is_expired():
    print("メニューが期限切れです")
```

---

## データベーススキーマ

### テーブル作成

スキーマは `db/init/02-line-rich-menu-schema.sql` で定義されています。

**主要テーブル:**

1. **line_channels**: LINEチャネル設定
2. **rich_menus**: リッチメニュー定義
3. **user_rich_menus**: ユーザー・メニュー紐付け

**ビュー:**

1. **v_rich_menu_usage**: アクティブなメニューとユーザー数の集計
2. **v_channel_menu_stats**: チャネルごとのメニュー統計

### インデックス設計

効率的なクエリのために以下のインデックスが設定されています:

- `line_channels.channel_id` (UNIQUE)
- `rich_menus.rich_menu_line_id` (UNIQUE)
- `rich_menus.channel_id`, `name`, `is_active`
- `user_rich_menus.user_id`, `line_user_id`, `rich_menu_id`

---

## セットアップ手順

### Step 1: 環境準備

```bash
# Dockerコンテナ起動
cd schedule-coordinator-bot
docker-compose up -d

# バックエンドコンテナに接続
docker exec -it schedule-coordinator-backend bash
```

### Step 2: 依存関係インストール

```bash
# Poetryで依存関係をインストール
poetry install

# または個別にインストール
poetry add sqlalchemy mysql-connector-python python-dotenv
```

### Step 3: データベース初期化

```bash
# MySQLに接続してスキーマを確認
docker exec -it schedule-coordinator-db mysql -udevuser -pdevpass123 calendar_db

# スキーマが自動適用されているか確認
SHOW TABLES;

# line_channels, rich_menus, user_rich_menus テーブルが存在すればOK
```

### Step 4: モデルテスト実行

```bash
# バックエンドディレクトリで
cd /app
python test_models.py
```

**期待される出力:**

```
============================================================
LINE Bot チャネル設定・リッチメニュー定義 モデルテスト
============================================================

============================================================
テスト 1: データベース接続確認
============================================================
✅ データベース接続成功

...

合計: 5/5 テスト合格

🎉 すべてのテストが成功しました！
```

---

## 使用方法

### FastAPIとの統合

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.line_channel import LineChannel
from models.rich_menu import RichMenu

app = FastAPI()

@app.get("/channels")
def get_channels(db: Session = Depends(get_db)):
    """全チャネルを取得"""
    channels = db.query(LineChannel).filter(
        LineChannel.is_active == 1
    ).all()
    return [ch.to_dict() for ch in channels]

@app.get("/rich-menus/{channel_id}")
def get_rich_menus(channel_id: int, db: Session = Depends(get_db)):
    """特定チャネルのリッチメニューを取得"""
    menus = db.query(RichMenu).filter(
        RichMenu.channel_id == channel_id,
        RichMenu.is_active == 1
    ).all()
    return [menu.to_dict(include_definition=True) for menu in menus]

@app.post("/user/{user_id}/rich-menu/{menu_id}")
def set_user_menu(
    user_id: str,
    menu_id: int,
    db: Session = Depends(get_db)
):
    """ユーザーにリッチメニューを設定"""
    # 既存の有効なメニューを無効化
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
    
    return {"message": "メニュー設定完了"}
```

---

## テスト手順

### 単体テスト

```bash
# モデルテストスクリプト実行
python test_models.py
```

### 手動テスト（MySQL CLI）

```sql
-- チャネルを作成
INSERT INTO line_channels (
    channel_id, channel_name, channel_access_token, 
    channel_secret, webhook_url
) VALUES (
    'test_12345', 'Test Bot', 'token_abc', 
    'secret_xyz', 'https://example.com/webhook'
);

-- リッチメニューを作成
INSERT INTO rich_menus (
    rich_menu_line_id, channel_id, name, 
    rich_menu_json_definition
) VALUES (
    'richmenu-001', 1, 'main_menu',
    '{"size": {"width": 2500, "height": 1686}, "areas": []}'
);

-- JSON クエリテスト
SELECT 
    name,
    JSON_EXTRACT(rich_menu_json_definition, '$.size.width') AS width,
    JSON_EXTRACT(rich_menu_json_definition, '$.size.height') AS height
FROM rich_menus;

-- ビューを使った統計取得
SELECT * FROM v_rich_menu_usage;
SELECT * FROM v_channel_menu_stats;
```

---

## API統合例

### LINE Messaging APIとの連携

```python
import requests
from models.line_channel import LineChannel
from models.rich_menu import RichMenu

def create_rich_menu_on_line(channel: LineChannel, menu: RichMenu):
    """LINEプラットフォームにリッチメニューを作成"""
    url = "https://api.line.me/v2/bot/richmenu"
    headers = {
        "Authorization": f"Bearer {channel.channel_access_token}",
        "Content-Type": "application/json"
    }
    
    # データベースから取得したJSON定義を使用
    response = requests.post(
        url,
        headers=headers,
        json=menu.rich_menu_json_definition
    )
    
    if response.status_code == 200:
        rich_menu_id = response.json()["richMenuId"]
        # データベースに保存
        menu.rich_menu_line_id = rich_menu_id
        db.commit()
        return rich_menu_id
    
    return None

def link_rich_menu_to_user(
    channel: LineChannel,
    line_user_id: str,
    rich_menu_line_id: str
):
    """ユーザーにリッチメニューをリンク"""
    url = f"https://api.line.me/v2/bot/user/{line_user_id}/richmenu/{rich_menu_line_id}"
    headers = {
        "Authorization": f"Bearer {channel.channel_access_token}"
    }
    
    response = requests.post(url, headers=headers)
    return response.status_code == 200
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. データベース接続エラー

```bash
# コンテナが起動しているか確認
docker ps

# データベースコンテナのログ確認
docker logs schedule-coordinator-db

# 環境変数確認
docker exec schedule-coordinator-backend env | grep DATABASE
```

#### 2. JSON型のエラー

MySQLのバージョンが5.7.8以上であることを確認してください。

```sql
SELECT VERSION();
```

#### 3. 外部キー制約エラー

関連するレコードが存在するか確認:

```sql
-- チャネルが存在するか
SELECT * FROM line_channels WHERE id = 1;

-- リッチメニューが存在するか
SELECT * FROM rich_menus WHERE id = 1;
```

---

## まとめ

このガイドに従うことで、LINE Botのチャネル設定とリッチメニュー定義を効率的に管理するシステムを構築できます。

### 次のステップ

1. LINE Messaging APIとの完全な統合
2. 管理画面UIの実装
3. メニュー切り替えロジックの実装
4. アナリティクス機能の追加

### 参考リンク

- [LINE Messaging API Documentation](https://developers.line.biz/ja/docs/messaging-api/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
