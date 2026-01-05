# Schedule Coordinator Bot - React Frontend

このプロジェクトは、ReactでGoogleカレンダー連携機能を実装したスケジュール調整ボットのフロントエンドアプリケーションです。

## セットアップ手順

### 1. 依存パッケージのインストール

```bash
npm install
```

### 2. 環境変数の設定

`.env`ファイルを編集し、以下の環境変数を設定します：

```env
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id-here.apps.googleusercontent.com
REACT_APP_BACKEND_URL=http://localhost:8000
```

- `REACT_APP_GOOGLE_CLIENT_ID`: Google Cloud ConsoleからOAuth 2.0クライアントIDを取得して設定
- `REACT_APP_BACKEND_URL`: バックエンドAPIのURL

### 3. Google Cloud Consoleの設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. 「APIとサービス」→「認証情報」から「OAuth 2.0クライアントID」を作成
3. 承認済みのリダイレクトURIに以下を追加：
   - `http://localhost:3000/auth/google/callback`

### 4. バックエンドAPIの準備

以下のエンドポイントがバックエンド（FastAPI）で実装されている必要があります：

- `GET /api/auth/google/login` - Google認証開始URLを返す
- `POST /api/auth/google/callback` - 認証コールバック処理
- `GET /api/user/calendar-status` - ユーザーの連携状態を取得
- `POST /api/auth/google/disconnect` - 連携解除

### 5. アプリケーションの起動

```bash
npm start
```

ブラウザで `http://localhost:3000` にアクセスします。

## プロジェクト構造

```
src/
├── components/
│   └── GoogleCalendarConnectButton.jsx  # カレンダー連携ボタンコンポーネント
├── pages/
│   └── AuthCallback.jsx                 # 認証コールバックページ
├── App.jsx                              # メインアプリケーションとルーティング
├── index.js                             # エントリーポイント
└── index.css                            # グローバルスタイル
```

## 機能

- **Googleカレンダー連携**: Googleアカウントでログインし、カレンダーへのアクセスを許可
- **連携状態表示**: 現在の連携状態（連携済み/未連携）を表示
- **連携解除**: 既存の連携を解除
- **認証コールバック処理**: Google認証後のコールバック処理とエラーハンドリング

## 使用ライブラリ

- **React 18**: UIライブラリ
- **react-router-dom**: ルーティング
- **@react-oauth/google**: Google OAuth統合
- **axios**: HTTP通信

## トラブルシューティング

### CORS エラーが発生する場合

バックエンドAPIでCORS設定が正しく行われているか確認してください。

### 認証がリダイレクトされない場合

- `.env`ファイルの`REACT_APP_GOOGLE_CLIENT_ID`が正しく設定されているか確認
- Google Cloud ConsoleでリダイレクトURIが正しく登録されているか確認

## ライセンス

MIT
