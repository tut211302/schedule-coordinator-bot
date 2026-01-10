"""
Database Models Test Script
LINE Bot チャネル設定とリッチメニュー定義のテスト
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, check_db_connection, init_db
from models.line_channel import LineChannel
from models.rich_menu import RichMenu
from models.user_rich_menu import UserRichMenu


def test_database_connection():
    """テスト 1: データベース接続確認"""
    print("\n" + "="*60)
    print("テスト 1: データベース接続確認")
    print("="*60)
    
    if check_db_connection():
        print("✅ データベース接続成功")
        return True
    else:
        print("❌ データベース接続失敗")
        return False


def test_line_channel_crud():
    """テスト 2: LINE Channel モデルのCRUD操作"""
    print("\n" + "="*60)
    print("テスト 2: LINE Channel モデルのCRUD操作")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Create
        print("\n📝 チャネル作成テスト...")
        channel = LineChannel(
            channel_id="test_channel_12345",
            channel_name="Test Schedule Bot",
            channel_access_token="test_access_token_abcdefg123456789",
            channel_secret="test_secret_xyz",
            webhook_url="https://test-domain.com/webhook",
            is_active=1
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)
        print(f"✅ チャネル作成成功: {channel}")
        
        # Read
        print("\n🔍 チャネル取得テスト...")
        retrieved = db.query(LineChannel).filter(
            LineChannel.channel_id == "test_channel_12345"
        ).first()
        if retrieved:
            print(f"✅ チャネル取得成功: {retrieved.channel_name}")
            print(f"   to_dict(): {retrieved.to_dict()}")
        
        # Update
        print("\n✏️ チャネル更新テスト...")
        retrieved.channel_name = "Updated Test Bot"
        db.commit()
        print(f"✅ チャネル更新成功: {retrieved.channel_name}")
        
        # List
        print("\n📋 全チャネル取得テスト...")
        all_channels = db.query(LineChannel).all()
        print(f"✅ チャネル数: {len(all_channels)}")
        for ch in all_channels:
            print(f"   - {ch.channel_name} (ID: {ch.channel_id})")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_rich_menu_crud():
    """テスト 3: Rich Menu モデルのCRUD操作"""
    print("\n" + "="*60)
    print("テスト 3: Rich Menu モデルのCRUD操作")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Get channel for foreign key
        channel = db.query(LineChannel).first()
        if not channel:
            print("❌ チャネルが存在しません。先にtest_line_channel_crud()を実行してください。")
            return False
        
        # Create Rich Menu with JSON definition
        print("\n📝 リッチメニュー作成テスト...")
        rich_menu_json = {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": True,
            "name": "Test Menu",
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
                },
                {
                    "bounds": {
                        "x": 1250,
                        "y": 0,
                        "width": 1250,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "予定を登録"
                    }
                }
            ]
        }
        
        menu = RichMenu(
            rich_menu_line_id="richmenu-test-001",
            channel_id=channel.id,
            name="test_main_menu",
            display_name="テストメインメニュー",
            image_url="https://example.com/menu.png",
            rich_menu_json_definition=rich_menu_json,
            description="テスト用のメインメニュー",
            is_active=1,
            is_default=1
        )
        db.add(menu)
        db.commit()
        db.refresh(menu)
        print(f"✅ リッチメニュー作成成功: {menu}")
        
        # Read and test methods
        print("\n🔍 リッチメニュー取得テスト...")
        retrieved = db.query(RichMenu).filter(
            RichMenu.rich_menu_line_id == "richmenu-test-001"
        ).first()
        if retrieved:
            print(f"✅ リッチメニュー取得成功: {retrieved.name}")
            print(f"   Areas: {retrieved.get_menu_areas()}")
            print(f"   Size: {retrieved.get_menu_size()}")
            print(f"   to_dict(): {retrieved.to_dict()}")
        
        # Query JSON fields
        print("\n🔍 JSON フィールドクエリテスト...")
        menus = db.query(RichMenu).all()
        for m in menus:
            json_def = m.rich_menu_json_definition
            print(f"   Menu: {m.name}")
            print(f"   - Size: {json_def.get('size')}")
            print(f"   - Chat Bar Text: {json_def.get('chatBarText')}")
            print(f"   - Areas Count: {len(json_def.get('areas', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_user_rich_menu_crud():
    """テスト 4: User Rich Menu モデルのCRUD操作"""
    print("\n" + "="*60)
    print("テスト 4: User Rich Menu モデルのCRUD操作")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Get rich menu for foreign key
        menu = db.query(RichMenu).first()
        if not menu:
            print("❌ リッチメニューが存在しません。先にtest_rich_menu_crud()を実行してください。")
            return False
        
        # Create user-menu binding
        print("\n📝 ユーザー・メニュー紐付け作成テスト...")
        user_menu = UserRichMenu(
            user_id="user_12345",
            line_user_id="U1234567890abcdef",
            rich_menu_id=menu.id,
            is_active=1,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(user_menu)
        db.commit()
        db.refresh(user_menu)
        print(f"✅ 紐付け作成成功: {user_menu}")
        
        # Read with relationship
        print("\n🔍 紐付け取得テスト（リレーション含む）...")
        retrieved = db.query(UserRichMenu).filter(
            UserRichMenu.user_id == "user_12345"
        ).first()
        if retrieved:
            print(f"✅ 紐付け取得成功")
            print(f"   User: {retrieved.user_id}")
            print(f"   Menu: {retrieved.rich_menu.name}")
            print(f"   Is Expired: {retrieved.is_expired()}")
            print(f"   to_dict(): {retrieved.to_dict(include_rich_menu=True)}")
        
        # Test expiration
        print("\n⏰ 有効期限テスト...")
        expired_menu = UserRichMenu(
            user_id="user_67890",
            line_user_id="U0987654321fedcba",
            rich_menu_id=menu.id,
            is_active=1,
            expires_at=datetime.utcnow() - timedelta(days=1)  # 昨日で期限切れ
        )
        db.add(expired_menu)
        db.commit()
        db.refresh(expired_menu)
        print(f"   期限切れメニュー: {expired_menu.is_expired()}")
        if expired_menu.is_expired():
            print("   ✅ 期限切れ判定正常")
        
        # List all user menus
        print("\n📋 全ユーザー・メニュー紐付け取得テスト...")
        all_user_menus = db.query(UserRichMenu).all()
        print(f"✅ 紐付け数: {len(all_user_menus)}")
        for um in all_user_menus:
            print(f"   - User {um.user_id} -> Menu {um.rich_menu.name} (Active: {bool(um.is_active)})")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_relationships():
    """テスト 5: モデル間のリレーションシップテスト"""
    print("\n" + "="*60)
    print("テスト 5: モデル間のリレーションシップテスト")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Test Channel -> Rich Menus relationship
        print("\n🔗 Channel -> Rich Menus リレーションテスト...")
        channel = db.query(LineChannel).first()
        if channel:
            print(f"   Channel: {channel.channel_name}")
            print(f"   Rich Menus: {len(channel.rich_menus)}")
            for menu in channel.rich_menus:
                print(f"     - {menu.name} ({menu.display_name})")
            print("✅ リレーション取得成功")
        
        # Test Rich Menu -> User Rich Menus relationship
        print("\n🔗 Rich Menu -> User Rich Menus リレーションテスト...")
        menu = db.query(RichMenu).first()
        if menu:
            print(f"   Rich Menu: {menu.name}")
            print(f"   Linked Users: {len(menu.user_rich_menus)}")
            for um in menu.user_rich_menus:
                print(f"     - User {um.user_id} (Active: {bool(um.is_active)})")
            print("✅ リレーション取得成功")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        db.close()


def cleanup_test_data():
    """テストデータのクリーンアップ"""
    print("\n" + "="*60)
    print("テストデータのクリーンアップ")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Delete test user menus
        db.query(UserRichMenu).filter(
            UserRichMenu.user_id.like("user_%")
        ).delete(synchronize_session=False)
        
        # Delete test rich menus
        db.query(RichMenu).filter(
            RichMenu.rich_menu_line_id.like("richmenu-test-%")
        ).delete(synchronize_session=False)
        
        # Delete test channels
        db.query(LineChannel).filter(
            LineChannel.channel_id.like("test_channel_%")
        ).delete(synchronize_session=False)
        
        db.commit()
        print("✅ テストデータのクリーンアップ完了")
        return True
        
    except Exception as e:
        print(f"❌ クリーンアップエラー: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """メインテスト実行関数"""
    print("\n" + "="*60)
    print("LINE Bot チャネル設定・リッチメニュー定義 モデルテスト")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("データベース接続", test_database_connection()))
    results.append(("LINE Channel CRUD", test_line_channel_crud()))
    results.append(("Rich Menu CRUD", test_rich_menu_crud()))
    results.append(("User Rich Menu CRUD", test_user_rich_menu_crud()))
    results.append(("リレーションシップ", test_relationships()))
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
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
    else:
        print("\n⚠️  一部のテストが失敗しました。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
