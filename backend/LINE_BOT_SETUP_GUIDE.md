# LINE Bot 統合セットアップ手順（Docker版）

## 概要

本ガイドでは、Docker Compose を使用してLINE Bot統合環境を構築し、実装したデータベースモデルをLINE Messaging APIと連携させるセットアップ手順を説明します。

## 前提条件

- Docker Desktop がインストール済みであること
- Docker daemon が起動していること

Docker Desktop のインストール方法：
- Windows: https://www.docker.com/products/docker-desktop
- Mac: https://www.docker.com/products/docker-desktop
- Linux: Docker公式ドキュメント参照

## ステップ 1: 必要なファイルの確認

以下のファイルが存在することを確認してください：

```
schedule-coordinator-bot/
├── docker-compose.yml        # Docker Compose設定
├── backend/
│   ├── Dockerfile            # バックエンド用Docker設定
│   ├── models/
│   │   ├── __init__.py       # モデル定義
│   │   ├── line_channel.py   # LINEチャネルモデル
│   │   ├── rich_menu.py      # リッチメニューモデル
│   │   └── user_rich_menu.py # ユーザーメニュー関連モデル
│   ├── database.py           # SQLAlchemy設定
│   ├── line_bot_test.py      # テストコード
│   ├── fastapi_line_webhook.py # FastAPI統合
│   ├── main.py               # メインアプリケーション
│   └── pyproject.toml        # Python依存関係定義
├── db/
│   ├── Dockerfile            # MySQL用Docker設定
│   └── init/
│       ├── 01-schema.sql     # テーブル定義
│       └── 02-line-rich-menu-schema.sql
└── frontend/
    └── Dockerfile            # フロントエンド用Docker設定
```

## ステップ 2: 環境変数の設定

### 2.1 `.env` ファイルを作成

**プロジェクトルート**（`schedule-coordinator-bot/`）に `.env` ファイルを作成し、以下の内容を記入してください：

```env
# DATABASE設定（Docker内での接続）
DATABASE_URL=mysql+mysqlconnector://devuser:devpass123@db:3306/calendar_db

# LINE Messaging API設定
LINE_CHANNEL_ID=1234567890
LINE_CHANNEL_SECRET=your_channel_secret_here
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here

# Webhook設定（ngrok使用時）
LINE_WEBHOOK_URL=https://xxxx-xx-xxx-xx-xx.ngrok.io/webhook/line

# アプリケーション設定
DEBUG=true
LOG_LEVEL=INFO

# Docker設定
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
```

**重要**: 
- Docker環境では `DATABASE_URL` のホストは `db`（サービス名）を使用します
- ローカル環境の場合と異なるため注意してください

### 2.2 LINE Developers Consoleから認証情報を取得

1. [LINE Developers](https://developers.line.biz/ja/) にアクセス
2. ビジネス用アカウントでログイン
3. 「Create New Channel」でMessaging APIチャネルを作成
4. 「Channel settings」から以下を確認・コピー：
   - Channel ID
   - Channel Secret
   - Channel Access Token

5. `.env` ファイルに記入

**重要**: Channel Secret と Access Token は絶対に共有しないでください。

## ステップ 3: Docker Compose でのセットアップ

### 3.1 Docker Desktop の起動確認

Docker がインストール済みで起動していることを確認してください：

```powershell
docker --version
```

バージョン情報が表示されれば成功です。起動していない場合は Docker Desktop を起動してください。

### 3.2 Docker Compose でコンテナを起動

```powershell
cd schedule-coordinator-bot

# コンテナをビルド・起動
docker-compose up -d
```

このコマンドで以下が自動で起動します：
- **MySQL データベース**（ポート：3306）
- **FastAPI バックエンド**（ポート：8000）
- **フロントエンド**（ポート：3000）

### 3.3 起動状況を確認

```powershell
# コンテナ起動確認
docker-compose ps

# 期待される出力：
# NAME                          COMMAND                  STATUS
# schedule-coordinator-bot-db   "docker-entrypoint..."  Up 
# schedule-coordinator-bot-backend "uvicorn main:app..."  Up
# schedule-coordinator-bot-frontend "npm start"          Up
```

### 3.4 ログを確認

```powershell
# すべてのログを表示
docker-compose logs -f

# バックエンドのログのみ表示
docker-compose logs -f backend

# データベースのログのみ表示
docker-compose logs -f db
```

期待されるログ：
```
backend  | INFO:     Uvicorn running on http://0.0.0.0:8000
backend  | INFO:     Application startup complete
db       | [Note] Event Scheduler: Loaded 0 events
```

## ステップ 4: データベースの初期化

### 4.1 初期化スクリプトを実行（Docker）

```powershell
# バックエンドコンテナ内で初期化スクリプトを実行
docker-compose exec backend python -c "from database import init_db; init_db()"
```

### 4.2 初期化が成功したか確認

```powershell
docker-compose exec backend python -c "from database import check_db_connection; check_db_connection()"
```

期待される出力：
```
✅ Database connection successful
✅ Tables created:
  - line_channels
  - rich_menus
  - user_rich_menus
```

### 4.3 MySQL に直接接続して確認（オプション）

```powershell
# MySQL コンテナにアクセス
docker-compose exec db mysql -u devuser -pdevpass123 calendar_db

# テーブルを確認
mysql> SHOW TABLES;
```

## ステップ 5: LINE Developers Console での設定

### 5.1 Webhook URL を設定

Docker で実行する場合、ngrok を使用してトンネルを作成する必要があります。

#### ngrok のインストール（初回のみ）

**Windows:**
```powershell
# chocolatey を使用
choco install ngrok

# または pip を使用
pip install pyngrok
```

**Mac:**
```bash
brew install ngrok
```

#### ngrok でトンネルを作成

```powershell
ngrok http 8000
```

出力例：
```
ngrok                                       (Ctrl+C to quit)

Session Status                online
Account                       user@example.com
Version                        3.x.x
Region                         jp,us
Forwarding                     https://xxxx-xx-xxx-xx-xx.ngrok.io -> http://localhost:8000
Forwarding                     http://xxxx-xx-xxx-xx-xx.ngrok.io -> http://localhost:8000
```

#### LINE Developers Console でWebhook URL を登録

1. [LINE Developers](https://developers.line.biz/ja/) を開く
2. 該当チャネルの「Messaging API settings」を選択
3. 「Webhook settings」セクションを探す
4. 「Webhook URL」に ngrok の URL を入力：
   ```
   https://xxxx-xx-xxx-xx-xx.ngrok.io/webhook/line
   ```
5. 「Update」をクリック

### 5.2 Webhook の検証を有効にする

1. 同じ「Webhook settings」セクション内
2. 「Use webhook」トグルを有効化（ON）
3. 「Verify」ボタンをクリック

期待される結果：
```
✅ Connected
```

## ステップ 6: アプリケーションアクセス

### 6.1 FastAPI サーバーの確認

```powershell
# ヘルスチェック
curl http://localhost:8000/health

# 期待される出力
{"status":"healthy"}
```

### 6.2 FastAPI Swagger UI（API ドキュメント）

ブラウザで以下にアクセス：
```
http://localhost:8000/docs
```

すべての API エンドポイントがインタラクティブに表示されます。

### 6.3 フロントエンド

```
http://localhost:3000
```

### 6.4 MySQL データベース接続

```powershell
# コンテナ内の MySQL に接続
docker-compose exec db mysql -u devuser -pdevpass123 calendar_db

# テーブル確認
mysql> SHOW TABLES;
mysql> SELECT * FROM line_channels;
```

## ステップ 7: テストの実行

### 7.1 LINE Bot セットアップテストを実行

```powershell
# バックエンドコンテナ内でテストを実行
docker-compose exec backend python line_bot_test.py
```

期待される出力：
```
============================================================
LINE Bot セットアップテスト
============================================================
✅ チャネル: My Schedule Bot
   Channel ID: 1234567890
   Webhook URL: https://xxxx-xx-xxx-xx-xx.ngrok.io/webhook/line
✅ LINE Bot API 接続成功
   Bot User ID: U1234567890abcdef1234567890abcdef
   Bot Name: Schedule Coordinator Bot
✅ リッチメニュー: 1 個
   - main_menu (メインメニュー)
     Active: True, Default: True

✅ セットアップテスト完了
🎉 すべてのテストが成功しました！
   LINEアプリからメッセージを送信してテストしてください
```

### 7.2 ユーザーメニュー管理テストを実行

```powershell
docker-compose exec backend python line_bot_test.py
```

テスト内容：
- LINE Bot API への接続確認
- チャネル情報の取得確認
- リッチメニューの取得確認
- ユーザーメニュー設定の確認

## ステップ 8: LINEアプリでのテスト

### 8.1 LINE で Bot をフォロー

1. LINEアプリを開く
2. 「友だち追加」を選択
3. 前述で作成したチャネルを検索
4. 「追加」をクリック

期待される結果：
- Bot からウェルカムメッセージが届く
- ユーザーがデータベースに登録される
- デフォルトメニューが自動設定される

### 8.2 テストメッセージを送信

Bot に以下のメッセージを送信してテストしてください：

| メッセージ | 期待される応答 |
|-----------|--------------|
| 予定を確認 | 📅 予定を確認します... |
| 予定を登録 | ➕ 新しい予定を登録します... |
| カレンダー連携 | 🔗 Googleカレンダーと連携します... |
| 設定 | ⚙️ 設定画面... |
| ヘルプ | ℹ️ ヘルプ情報を表示 |
| ステータス | 📊 ユーザーのステータス情報を表示 |

### 8.3 データベースで状態を確認

```powershell
# MySQL コンテナ内で確認
docker-compose exec db mysql -u devuser -pdevpass123 calendar_db -e "SELECT * FROM user_rich_menus WHERE is_active = 1\G"
```

## ステップ 9: API管理エンドポイントのテスト

### 9.1 チャネル一覧を取得

```powershell
curl http://localhost:8000/api/line/channels
```

期待される出力：
```json
{
  "status": "success",
  "channels": [
    {
      "id": 1,
      "channel_id": "1234567890",
      "channel_name": "Schedule Coordinator Bot",
      "webhook_url": "https://xxxx-xx-xxx-xx-xx.ngrok.io/webhook/line"
    }
  ]
}
```

### 9.2 チャネルのメニュー一覧を取得

```powershell
curl http://localhost:8000/api/line/channels/1234567890/menus
```

### 9.3 ユーザーのメニュー情報を取得

```powershell
curl http://localhost:8000/api/line/users/U1234567890abcdef/menu
```

### 9.4 ユーザーにメニューを設定

```powershell
curl -X POST http://localhost:8000/api/line/users/U1234567890abcdef/menu/1
```

## ステップ 10: トラブルシューティング

### 問題 1: Docker daemon が起動していない

**エラー:**
```
error during connect: this error may indicate that the docker daemon is not running
```

**解決策:**
1. Docker Desktop を起動
2. しばらく待機（初回は数十秒かかる場合があります）
3. 再度 `docker-compose up -d` を実行

### 問題 2: ポートがすでに使用中

**エラー:**
```
ERROR: for db  Cannot start service db: Ports are in use by another container
```

**解決策:**
```powershell
# 既存のコンテナを停止
docker-compose down

# または特定のコンテナを削除
docker-compose rm -f

# 再度起動
docker-compose up -d
```

### 問題 3: Webhook 署名が無効

**エラー:**
```
❌ Invalid signature
```

**原因:**
- Channel Secret が正しくない
- リクエストボディが改竄されている

**解決策:**
1. LINE Developers Console で Channel Secret を確認
2. `.env` ファイルを更新
3. バックエンドコンテナを再起動：
   ```powershell
   docker-compose restart backend
   ```

### 問題 4: LINE Bot API への接続失敗

**エラー:**
```
❌ LINE Bot API 接続失敗: 401 Client Error
```

**原因:**
- Channel Access Token が無効
- トークンが期限切れ

**解決策:**
1. LINE Developers Console で新しい Channel Access Token を再発行
2. `.env` ファイルを更新
3. テストを再実行

### 問題 5: Webhook が受信されない

**エラー:**
```
⚠️ Webhook not received
```

**原因:**
- ngrok が起動していない
- LINE Developers Console でWebhook URLが正しく設定されていない
- ファイアウォールがブロックしている

**解決策:**
1. ngrok が起動していることを確認：`curl http://localhost:4040/api/tunnels`
2. LINE Developers Console で Webhook URL を確認
3. Webhook の「Verify」ボタンをクリック

### 問題 6: データベース接続エラー

**エラー:**
```
❌ Error: (2003, "Can't connect to MySQL server")
```

**原因:**
- MySQL コンテナが起動していない
- データベース名が異なる

**解決策:**
1. MySQL コンテナが起動していることを確認：
   ```powershell
   docker-compose logs db
   ```
2. 初期化スクリプトが正常に実行されているか確認
3. `.env` ファイルの `DATABASE_URL` を確認

## ステップ 11: Docker 管理コマンド

### コンテナ管理

```powershell
# コンテナの起動
docker-compose up -d

# コンテナの停止
docker-compose stop

# コンテナの再起動
docker-compose restart

# コンテナの削除
docker-compose down

# 強制削除（キャッシュなし）
docker-compose down -v

# コンテナの状態確認
docker-compose ps

# コンテナの詳細確認
docker-compose logs backend
docker-compose logs db
docker-compose logs frontend
```

### ビルド管理

```powershell
# コンテナの再構築
docker-compose build

# 再構築して起動
docker-compose up -d --build

# キャッシュなしで再構築
docker-compose build --no-cache
```

### イメージ管理

```powershell
# イメージ一覧
docker images

# 不要なイメージを削除
docker image prune

# ボリューム一覧
docker volume ls

# ボリュームをクリア
docker volume prune
```

## ステップ 12: 次のステップ

1. **Googleカレンダー連携**: Google Calendar API と統合
2. **ユーザー認証**: OAuth2 認証の実装
3. **予定管理API**: 予定の登録・確認・更新・削除エンドポイント
4. **リッチメニュー自動生成**: テンプレートから動的に作成
5. **ロギング・監視**: Docker ログの設定と監視
6. **本番デプロイ**: Docker image を本番環境にデプロイ（AWS ECS / GCP Cloud Run など）

## 参考資料

- [Docker ドキュメント](https://docs.docker.com/)
- [Docker Compose ドキュメント](https://docs.docker.com/compose/)
- [LINE Developers](https://developers.line.biz/ja/)
- [LINE Messaging API ドキュメント](https://developers.line.biz/ja/docs/messaging-api/)
- [line-bot-sdk Python](https://github.com/line/line-bot-sdk-python)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
- [ngrok ドキュメント](https://ngrok.com/docs)

## サポート

問題が発生した場合：

1. Docker ログを確認：`docker-compose logs -f`
2. テストを実行：`docker-compose exec backend python line_bot_test.py`
3. FastAPI swagger で API を確認：`http://localhost:8000/docs`
4. LINE_BOT_TESTING_GUIDE.md でトラブルシューティングを参照

---

**作成日**: 2024-01-09
**更新日**: 2026-01-10
**バージョン**: 2.0.0（Docker版）
**ステータス**: Docker環境向け
