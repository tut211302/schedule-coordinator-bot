# プロジェクト構造ガイド

## 📂 ファイル・ディレクトリ構成

```
schedule-coordinator-bot/
├── .devcontainer/                          # VS Code Dev Container 設定
│   ├── devcontainer.json                   # メイン Dev Container 設定ファイル
│   ├── docker-compose.devcontainer.yml     # Dev Container 用 docker-compose オーバーライド
│   ├── post-create.sh                      # コンテナ作成後の初期化スクリプト
│   ├── dev-setup.sh                        # 手動セットアップスクリプト
│   ├── .devcontainer.env                   # 環境変数テンプレート
│   ├── QUICKSTART.md                       # クイックスタートガイド
│   ├── DEVCONTAINER_GUIDE.md               # Dev Container 詳細ガイド
│   └── DOCKER_CONFIG.md                    # Docker 設定詳細ガイド
│
├── db/                                      # データベース関連
│   ├── Dockerfile                          # MySQL 用 Dockerfile
│   └── init/
│       └── 01-schema.sql                   # MySQL 初期化スクリプト
│
├── src/                                     # フロントエンド React コード
│   ├── api/
│   │   └── googleAuth.js                   # Google Auth API ヘルパー
│   ├── components/
│   │   └── GoogleCalendarConnectButton.jsx # カレンダー連携ボタンコンポーネント
│   ├── pages/
│   │   └── AuthCallback.jsx                # 認証コールバックページ
│   ├── App.jsx                             # メインアプリケーション・ルーティング
│   ├── index.js                            # エントリーポイント（Google OAuth Provider）
│   └── index.css                           # グローバルスタイル
│
├── public/                                  # フロントエンド静的ファイル
│   └── index.html                          # HTML エントリーポイント
│
├── backend/                                 # バックエンド FastAPI コード
│   ├── Dockerfile                          # バックエンド用 Dockerfile
│   ├── main.py                             # FastAPI エントリーポイント
│   ├── pyproject.toml                      # Python 依存関係（Poetry）
│   └── .gitkeep                            # ディレクトリ配置用
│
├── docker-compose.yml                      # メイン Docker Compose 設定
├── frontend.Dockerfile                     # フロントエンド用 Dockerfile
│
├── .env                                     # 環境変数（.gitignore で除外）
├── .env.example                            # 環境変数テンプレート（version control）
├── .gitignore                              # Git 除外ファイル
├── package.json                            # Node.js 依存関係
├── package-lock.json                       # npm ロックファイル
│
├── README.md                               # プロジェクト概要
├── TEST_CHECKLIST.md                       # テスト手順チェックリスト
├── PROJECT_STRUCTURE.md                    # このファイル
└── .git/                                    # Git リポジトリ

```

## 🗂️ 主要ディレクトリの説明

### `.devcontainer/`
**VS Code Remote - Containers の設定ファイル群**

- **devcontainer.json**: VS Code がコンテナ接続時に読み込む主設定ファイル
- **docker-compose.devcontainer.yml**: Dev Container 専用の docker-compose オーバーライド設定
- **post-create.sh**: コンテナ作成後に実行される初期化スクリプト
- **ガイドドキュメント**: QUICKSTART.md, DEVCONTAINER_GUIDE.md, DOCKER_CONFIG.md

### `src/`
**フロントエンド React アプリケーション**

```
src/
├── api/
│   └── googleAuth.js              # Axios を使用した API 通信
├── components/
│   └── GoogleCalendarConnectButton.jsx  # メインの UI コンポーネント
├── pages/
│   └── AuthCallback.jsx           # Google OAuth コールバック処理
├── App.jsx                        # ルーティング設定
├── index.js                       # React エントリーポイント
└── index.css                      # グローバルスタイル
```

**特徴:**
- React Router による SPA ルーティング
- Google OAuth プロバイダーでラップ
- Axios による API 通信
- ステートレスな UI コンポーネント設計

### `backend/`
**バックエンド FastAPI アプリケーション**

```
backend/
├── Dockerfile                     # Python 3.11 ベース
├── main.py                        # FastAPI エントリーポイント
├── pyproject.toml                 # Poetry 依存関係定義
└── .gitkeep                       # ディレクトリ維持用
```

**特徴:**
- FastAPI + Uvicorn
- Poetry で依存関係管理
- MySQL データベース接続
- Google OAuth2 認証フロー実装予定

### `db/`
**データベース関連ファイル**

```
db/
├── Dockerfile                     # MySQL 8.0 ベース
└── init/
    └── 01-schema.sql             # テーブル定義
```

**スキーマ:**
- `users`: ユーザー情報・Google OAuth トークン
- `calendar_events`: 同期されたカレンダーイベント
- `sync_logs`: 同期ログ
- `oauth_states`: CSRF 保護用 state テーブル

## 📋 主要ファイルの説明

### `docker-compose.yml`
**全サービスのオーケストレーション定義**

```yaml
services:
  frontend:   # http://localhost:3000
  backend:    # http://localhost:8000
  db:         # localhost:3306
  phpmyadmin: # http://localhost:8080
```

### `.env` ファイル
**環境変数**（git 除外）

```env
REACT_APP_GOOGLE_CLIENT_ID=...
REACT_APP_BACKEND_URL=http://localhost:8000
DATABASE_URL=mysql+mysqlconnector://...
```

### `package.json`
**フロントエンド依存関係**

**主な依存関係:**
- react, react-dom
- react-router-dom
- @react-oauth/google
- axios

### `backend/pyproject.toml`
**バックエンド依存関係**

**主な依存関係:**
- fastapi
- uvicorn
- sqlalchemy
- mysql-connector-python
- google-auth, google-auth-oauthlib

## 🔄 データフロー

### Google 認証フロー

```
1. ユーザー: 「Googleカレンダーと連携する」をクリック
   ↓
2. フロントエンド: GET /api/auth/google/login
   ↓
3. バックエンド: Google 認証 URL を返す
   ↓
4. フロントエンド: Google 認証ページにリダイレクト
   ↓
5. ユーザー: Google ログイン・権限許可
   ↓
6. Google: リダイレクト → http://localhost:3000/auth/google/callback?code=...
   ↓
7. フロントエンド: POST /api/auth/google/callback
   ↓
8. バックエンド: コード ↔ アクセストークン交換
   ↓
9. バックエンド: トークンを DB に保存
   ↓
10. フロントエンド: メインページに遷移
```

### 連携状態表示フロー

```
1. フロントエンド: GET /api/user/calendar-status
   ↓
2. バックエンド: DB からユーザー情報を取得
   ↓
3. バックエンド: { isConnected, email } を返す
   ↓
4. フロントエンド: 連携状態を表示
   - 連携済み → 「連携済み」バッジ + メールアドレス + 「連携解除」ボタン
   - 未連携   → 「未連携」バッジ + 「Googleカレンダーと連携する」ボタン
```

## 🧩 コンポーネント構成

### React コンポーネント構造

```
App
├── Route: "/" 
│   └── GoogleCalendarConnectButton
│       ├── Status Display
│       ├── Connect Button (未連携時)
│       └── Disconnect Button (連携済み時)
└── Route: "/auth/google/callback"
    └── AuthCallback
        ├── Loading State
        ├── Success State
        └── Error State
```

## 🔌 API エンドポイント

### フロントエンド → バックエンド

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/auth/google/login` | Google 認証 URL 取得 |
| POST | `/api/auth/google/callback` | 認証コード ↔ トークン交換 |
| GET | `/api/user/calendar-status` | 連携状態取得 |
| POST | `/api/auth/google/disconnect` | 連携解除 |

## 🚀 起動シーケンス

### Dev Container 起動時

```
1. docker-compose build                    # イメージビルド
   ├── frontend イメージ: Node.js 18
   ├── backend イメージ: Python 3.11
   └── db イメージ: MySQL 8.0

2. docker-compose up -d                    # コンテナ起動
   ├── backend: poetry install + sleep
   ├── frontend: npm install 完了
   └── db: MySQL 起動

3. post-create.sh 実行                     # 初期化処理
   ├── npm install (frontend)
   ├── poetry install (backend)
   ├── DB 待機
   └── .env ファイル生成

4. VS Code 接続                            # 開発開始
```

## 🔐 セキュリティ考慮

### 開発環境

- .env ファイルで簡単な認証情報使用
- CORS は localhost のみ許可
- CSRF 保護用 state パラメータ実装

### 本番環境

- 強力なシークレットキー使用
- CORS の詳細設定
- HTTPS 必須
- リレートリミット実装

## 📊 ボリューム・マウント

```yaml
Volumes:
  db_data:                          # MySQL データベースデータ永続化
  /workspace/node_modules:          # フロントエンド node_modules
  ./backend:/app:                   # バックエンドコード（ホットリロード用）
  ./src:/workspace/src:             # フロントエンドコード（ホットリロード用）
```

## 🆔 ネットワーク

```
Service Name  | Container Name    | Port | Network
--------------|-------------------|------|----------
frontend      | calendar-frontend | 3000 | dev-network
backend       | calendar-backend  | 8000 | dev-network
db            | calendar-db       | 3306 | dev-network
phpmyadmin    | calendar-phpmyadmin | 8080 | dev-network
```

**ホスト ↔ コンテナ通信:**
```
ホスト側: localhost:3000 → フォワード → コンテナ frontend:3000
ホスト側: localhost:8000 → フォワード → コンテナ backend:8000
```

## 📚 関連ドキュメント

- [.devcontainer/QUICKSTART.md](.devcontainer/QUICKSTART.md) - 素早く始める
- [.devcontainer/DEVCONTAINER_GUIDE.md](.devcontainer/DEVCONTAINER_GUIDE.md) - 詳細ガイド
- [.devcontainer/DOCKER_CONFIG.md](.devcontainer/DOCKER_CONFIG.md) - Docker 詳細
- [README.md](README.md) - プロジェクト概要
- [TEST_CHECKLIST.md](TEST_CHECKLIST.md) - テスト手順

---

**最終更新**: 2026年1月5日
