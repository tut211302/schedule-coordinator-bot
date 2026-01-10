import os

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
BOT_MENTION = os.getenv("BOT_MENTION", "").strip()  # 例: "@schedule-bot"
LINE_REPLY_ENDPOINT = "https://api.line.me/v2/bot/message/reply"
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
LIFF_ID = os.getenv("LIFF_ID", "")
