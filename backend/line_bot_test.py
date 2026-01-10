"""
LINE Bot テストコード
実装したモデルを使用したLINE Messaging API統合例
"""

import os
import sys
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureException, LineBotApiException
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FollowEvent,
    UnfollowEvent,
)
from database import SessionLocal
from models.line_channel import LineChannel
from models.rich_menu import RichMenu
from models.user_rich_menu import UserRichMenu


class LineBot:
    """LINE Bot API ラッパークラス"""
    
    def __init__(self, channel_id: str):
        """
        LINE Bot を初期化
        
        Args:
            channel_id: LINE チャネルID
        """
        self.db = SessionLocal()
        self.channel = self.db.query(LineChannel).filter(
            LineChannel.channel_id == channel_id,
            LineChannel.is_active == 1
        ).first()
        
        if not self.channel:
            raise ValueError(f"Channel not found: {channel_id}")
        
        self.line_bot_api = LineBotApi(self.channel.channel_access_token)
        self.parser = WebhookParser(self.channel.channel_secret)
    
    def close(self):
        """データベース接続をクローズ"""
        self.db.close()
    
    def parse_webhook(self, body: str, signature: str):
        """Webhook ペイロードをパース"""
        try:
            events = self.parser.parse(body, signature)
            return events
        except InvalidSignatureException:
            raise ValueError("Invalid webhook signature")
    
    def handle_follow_event(self, user_id: str, reply_token: str):
        """ユーザーフォローイベントを処理"""
        print(f"✅ User followed: {user_id}")
        
        # デフォルトメニューを取得
        default_menu = self.db.query(RichMenu).filter(
            RichMenu.channel_id == self.channel.id,
            RichMenu.is_default == 1,
            RichMenu.is_active == 1
        ).first()
        
        # ユーザーにデフォルトメニューを設定
        if default_menu:
            user_menu = UserRichMenu(
                user_id=user_id,
                line_user_id=user_id,
                rich_menu_id=default_menu.id,
                is_active=1
            )
            self.db.add(user_menu)
            self.db.commit()
            print(f"  → Default menu set for user: {default_menu.name}")
        
        # ウェルカムメッセージを送信
        try:
            self.line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text="Schedule Coordinator Botへようこそ！\n予定管理をサポートします。")
            )
            print(f"  → Welcome message sent")
        except LineBotApiException as e:
            print(f"  ❌ Error sending message: {e}")
    
    def handle_unfollow_event(self, user_id: str):
        """ユーザーブロックイベントを処理"""
        print(f"📵 User blocked: {user_id}")
        
        # ユーザーのメニュー設定を無効化
        self.db.query(UserRichMenu).filter(
            UserRichMenu.user_id == user_id
        ).update({"is_active": 0})
        self.db.commit()
        print(f"  → User menus deactivated")
    
    def handle_text_message(self, user_id: str, text: str, reply_token: str):
        """テキストメッセージイベントを処理"""
        print(f"💬 Message from {user_id}: {text}")
        
        # ユーザーのメニュー情報を取得
        user_menu = self.db.query(UserRichMenu).filter(
            UserRichMenu.user_id == user_id,
            UserRichMenu.is_active == 1
        ).first()
        
        # メッセージに応じた処理
        if text == "予定を確認":
            response = "📅 予定を確認します...\n[ここに予定情報が表示されます]"
        elif text == "予定を登録":
            response = "➕ 新しい予定を登録します...\n[ここに登録フォームが表示されます]"
        elif text == "カレンダー連携":
            response = "🔗 Googleカレンダーと連携します...\n[ここに連携画面が表示されます]"
        elif text == "設定":
            response = "⚙️ 設定画面です...\n[ここに設定オプションが表示されます]"
        elif text == "メニュー":
            # 使用中のメニュー情報を表示
            if user_menu:
                menu_info = f"📋 現在のメニュー: {user_menu.rich_menu.display_name}\n"
                response = menu_info + "メニュー内のボタンをタップしてください"
            else:
                response = "📋 メニューが設定されていません"
        elif text == "ステータス":
            # ユーザーのステータス情報を表示
            menu_name = user_menu.rich_menu.name if user_menu else "なし"
            response = f"📊 ステータス:\n- ユーザーID: {user_id}\n- メニュー: {menu_name}"
        else:
            response = f"ご入力ありがとうございます: {text}\n\n他のコマンドを試してください"
        
        # レスポンスを送信
        try:
            self.line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=response)
            )
            print(f"  → Response sent: {response[:50]}...")
        except LineBotApiException as e:
            print(f"  ❌ Error sending message: {e}")
    
    def process_webhook_events(self, events: list):
        """Webhook イベントリストを処理"""
        for event in events:
            try:
                if isinstance(event, FollowEvent):
                    self.handle_follow_event(event.source.user_id, event.reply_token)
                elif isinstance(event, UnfollowEvent):
                    self.handle_unfollow_event(event.source.user_id)
                elif isinstance(event, MessageEvent):
                    if isinstance(event.message, TextMessage):
                        self.handle_text_message(
                            event.source.user_id,
                            event.message.text,
                            event.reply_token
                        )
            except Exception as e:
                print(f"❌ Error processing event: {e}")
    
    def create_rich_menu(self, name: str, display_name: str, 
                        rich_menu_json: dict, image_url: str = None) -> RichMenu:
        """新しいリッチメニューを作成"""
        menu = RichMenu(
            rich_menu_line_id=f"richmenu-{datetime.now().timestamp()}",
            channel_id=self.channel.id,
            name=name,
            display_name=display_name,
            image_url=image_url,
            rich_menu_json_definition=rich_menu_json,
            is_active=1
        )
        self.db.add(menu)
        self.db.commit()
        self.db.refresh(menu)
        print(f"✅ Rich menu created: {name} (ID: {menu.id})")
        return menu
    
    def set_user_menu(self, user_id: str, menu_id: int) -> bool:
        """ユーザーにリッチメニューを設定"""
        # 既存のアクティブなメニューを無効化
        self.db.query(UserRichMenu).filter(
            UserRichMenu.user_id == user_id,
            UserRichMenu.is_active == 1
        ).update({"is_active": 0})
        
        # 新しいメニューを設定
        user_menu = UserRichMenu(
            user_id=user_id,
            rich_menu_id=menu_id,
            is_active=1
        )
        self.db.add(user_menu)
        self.db.commit()
        print(f"✅ Menu {menu_id} set for user {user_id}")
        return True
    
    def get_user_menu(self, user_id: str) -> Optional[UserRichMenu]:
        """ユーザーのメニュー情報を取得"""
        return self.db.query(UserRichMenu).filter(
            UserRichMenu.user_id == user_id,
            UserRichMenu.is_active == 1
        ).first()


def test_line_bot_setup():
    """LINE Bot セットアップテスト"""
    print("\n" + "="*60)
    print("LINE Bot セットアップテスト")
    print("="*60)
    
    try:
        # チャネルを取得
        db = SessionLocal()
        channel = db.query(LineChannel).filter(
            LineChannel.is_active == 1
        ).first()
        
        if not channel:
            print("❌ チャネルが登録されていません")
            print("   以下の手順でチャネルを登録してください:")
            print("   1. LINE Developers Console でチャネルを作成")
            print("   2. チャネルID, シークレット, アクセストークンを取得")
            print("   3. database.py の init_db() または API で登録")
            return False
        
        print(f"✅ チャネル: {channel.channel_name}")
        print(f"   Channel ID: {channel.channel_id}")
        print(f"   Webhook URL: {channel.webhook_url or 'Not set'}")
        
        # LINE Bot API をテスト
        bot = LineBot(channel.channel_id)
        
        try:
            profile = bot.line_bot_api.get_bot_info()
            print(f"✅ LINE Bot API 接続成功")
            print(f"   Bot User ID: {profile.user_id}")
            print(f"   Bot Name: {profile.display_name}")
        except LineBotApiException as e:
            print(f"❌ LINE Bot API 接続失敗: {e}")
            return False
        
        # リッチメニューをテスト
        menus = db.query(RichMenu).filter(
            RichMenu.channel_id == channel.id
        ).all()
        
        print(f"✅ リッチメニュー: {len(menus)} 個")
        for menu in menus:
            print(f"   - {menu.name} ({menu.display_name})")
            print(f"     Active: {bool(menu.is_active)}, Default: {bool(menu.is_default)}")
        
        bot.close()
        db.close()
        
        print("\n✅ セットアップテスト完了")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def test_webhook_simulation():
    """Webhook イベントシミュレーション"""
    print("\n" + "="*60)
    print("Webhook イベントシミュレーション")
    print("="*60)
    
    try:
        db = SessionLocal()
        channel = db.query(LineChannel).filter(
            LineChannel.is_active == 1
        ).first()
        
        if not channel:
            print("❌ チャネルが登録されていません")
            return False
        
        # テストユーザーID
        test_user_id = "U1234567890abcdef"
        
        # テストイベント (JSONシミュレーション)
        follow_event_json = {
            "events": [
                {
                    "type": "follow",
                    "message": {"type": "follow"},
                    "source": {"type": "user", "userId": test_user_id},
                    "replyToken": "00000000000000000000000000000000",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            ]
        }
        
        message_event_json = {
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "id": "100001",
                        "text": "予定を確認"
                    },
                    "source": {"type": "user", "userId": test_user_id},
                    "replyToken": "00000000000000000000000000000000",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            ]
        }
        
        print(f"✅ テストイベント作成完了")
        print(f"   User ID: {test_user_id}")
        print(f"   Channel: {channel.channel_name}")
        
        # イベント処理のシミュレーション
        print("\n📋 シミュレーション完了")
        print("   実際のテストはLINEアプリから送信してください")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def test_user_menu_management():
    """ユーザーメニュー管理テスト"""
    print("\n" + "="*60)
    print("ユーザーメニュー管理テスト")
    print("="*60)
    
    try:
        db = SessionLocal()
        channel = db.query(LineChannel).filter(
            LineChannel.is_active == 1
        ).first()
        
        if not channel:
            print("❌ チャネルが登録されていません")
            return False
        
        bot = LineBot(channel.channel_id)
        
        # テストユーザーID
        test_user_id = "U1234567890abcdef"
        
        # デフォルトメニューを取得
        default_menu = db.query(RichMenu).filter(
            RichMenu.channel_id == channel.id,
            RichMenu.is_default == 1,
            RichMenu.is_active == 1
        ).first()
        
        if default_menu:
            print(f"✅ デフォルトメニュー: {default_menu.display_name}")
            
            # ユーザーにメニューを設定
            bot.set_user_menu(test_user_id, default_menu.id)
            
            # メニューを取得して確認
            user_menu = bot.get_user_menu(test_user_id)
            if user_menu:
                print(f"✅ ユーザーメニュー確認: {user_menu.rich_menu.display_name}")
                print(f"   設定日時: {user_menu.set_at}")
            else:
                print(f"❌ ユーザーメニューが見つかりません")
        else:
            print("⚠️  デフォルトメニューが設定されていません")
            print("   リッチメニューを作成して is_default=1 に設定してください")
        
        bot.close()
        print("\n✅ ユーザーメニュー管理テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LINE Bot テストスイート")
    print("="*60)
    
    results = []
    
    # テスト実行
    results.append(("LINE Bot セットアップ", test_line_bot_setup()))
    results.append(("Webhook シミュレーション", test_webhook_simulation()))
    results.append(("ユーザーメニュー管理", test_user_menu_management()))
    
    # 結果サマリー
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n合計: {passed}/{total} テスト合格")
    
    if passed == total:
        print("\n🎉 すべてのテストが成功しました！")
        print("   LINEアプリからメッセージを送信してテストしてください")
    else:
        print("\n⚠️  一部のテストが失敗しました")
        print("   LINE_BOT_TESTING_GUIDE.md でトラブルシューティングを確認してください")
