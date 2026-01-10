"""
LINE Channel Model
管理LINE Botのチャネル設定情報
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from database import Base


class LineChannel(Base):
    """
    LINE Bot チャネル設定モデル
    
    LINE Messaging APIの認証情報およびWebhook設定を管理します。
    複数のチャネルを登録可能にすることで、開発環境と本番環境での
    切り替えや、複数のBotの運用に対応します。
    """
    __tablename__ = 'line_channels'

    # Primary Key
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
        comment='チャネル設定の内部ID'
    )
    
    # LINE Platform Information
    channel_id = Column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True,
        comment='LINE Developers Consoleで発行されるチャネルID'
    )
    
    channel_name = Column(
        String(255), 
        nullable=False,
        comment='チャネルの表示名（管理用）'
    )
    
    # Authentication Credentials
    channel_access_token = Column(
        String(512), 
        nullable=False,
        comment='Messaging API呼び出しに必要なアクセストークン'
    )
    
    channel_secret = Column(
        String(255), 
        nullable=False,
        comment='Webhook署名検証に必要なチャネルシークレット'
    )
    
    # Webhook Configuration
    webhook_url = Column(
        String(512), 
        nullable=True,
        comment='LINEプラットフォームからのイベントを受信するエンドポイントURL'
    )
    
    # Status
    is_active = Column(
        Integer,
        default=1,
        nullable=False,
        comment='チャネルの有効/無効状態 (1: 有効, 0: 無効)'
    )
    
    # Timestamps
    created_at = Column(
        DateTime, 
        server_default=func.now(),
        nullable=False,
        comment='作成日時'
    )
    
    updated_at = Column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False,
        comment='更新日時'
    )
    
    # Relationships
    # LineChannelに紐づくRichMenuのリレーション（逆参照）
    rich_menus = relationship(
        'RichMenu',
        back_populates='channel',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        """モデルの文字列表現"""
        return (
            f"<LineChannel("
            f"id={self.id}, "
            f"name='{self.channel_name}', "
            f"channel_id='{self.channel_id}', "
            f"is_active={self.is_active}"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """モデルを辞書形式に変換（API レスポンス用）"""
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'channel_name': self.channel_name,
            'webhook_url': self.webhook_url,
            'is_active': bool(self.is_active),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # セキュリティのため、トークンとシークレットは含めない
        }
