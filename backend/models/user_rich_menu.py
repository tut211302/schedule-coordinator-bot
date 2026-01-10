"""
User Rich Menu Model
管理ユーザーとリッチメニューの紐付け
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class UserRichMenu(Base):
    """
    ユーザー・リッチメニュー紐付けモデル
    
    どのユーザーにどのリッチメニューが現在適用されているかを管理します。
    これにより、ユーザーごとに異なるリッチメニューを表示したり、
    ユーザーの状態や行動に応じてメニューを動的に切り替えることができます。
    """
    __tablename__ = 'user_rich_menus'

    # Primary Key
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
        comment='紐付けレコードの内部ID'
    )
    
    # User Identification
    user_id = Column(
        String(255), 
        nullable=False,
        index=True,
        comment='アプリケーションのユーザーID（通常はLINEユーザーIDを使用）'
    )
    
    line_user_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment='LINE プラットフォームのユーザーID（U-xxxxx形式）'
    )
    
    # Foreign Key to RichMenu
    rich_menu_id = Column(
        Integer, 
        ForeignKey('rich_menus.id', ondelete='CASCADE'), 
        nullable=False,
        index=True,
        comment='ユーザーに紐付けられたリッチメニューのID'
    )
    
    # Status
    is_active = Column(
        Integer,
        default=1,
        nullable=False,
        comment='この紐付けの有効/無効状態 (1: 有効, 0: 無効)'
    )
    
    # Timestamps
    set_at = Column(
        DateTime, 
        server_default=func.now(),
        nullable=False,
        comment='リッチメニューが設定された日時'
    )
    
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment='更新日時（メニュー切り替え時など）'
    )
    
    expires_at = Column(
        DateTime,
        nullable=True,
        comment='リッチメニューの有効期限（期間限定メニュー用、NULLの場合は無期限）'
    )
    
    # Relationships
    rich_menu = relationship(
        'RichMenu',
        back_populates='user_rich_menus'
    )
    
    # Unique Constraint: 1ユーザーにつき1つの有効なリッチメニューのみ
    __table_args__ = (
        UniqueConstraint('user_id', 'is_active', name='uq_user_active_menu'),
        {'comment': 'ユーザーとリッチメニューの紐付けを管理'}
    )

    def __repr__(self) -> str:
        """モデルの文字列表現"""
        return (
            f"<UserRichMenu("
            f"id={self.id}, "
            f"user_id='{self.user_id}', "
            f"rich_menu_id={self.rich_menu_id}, "
            f"is_active={self.is_active}"
            f")>"
        )
    
    def to_dict(self, include_rich_menu: bool = False) -> dict:
        """
        モデルを辞書形式に変換（API レスポンス用）
        
        Args:
            include_rich_menu: リッチメニュー情報を含めるかどうか
        
        Returns:
            dict: モデルの辞書表現
        """
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'line_user_id': self.line_user_id,
            'rich_menu_id': self.rich_menu_id,
            'is_active': bool(self.is_active),
            'set_at': self.set_at.isoformat() if self.set_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }
        
        if include_rich_menu and self.rich_menu:
            result['rich_menu'] = self.rich_menu.to_dict()
        
        return result
    
    def is_expired(self) -> bool:
        """
        リッチメニューが期限切れかどうかを判定
        
        Returns:
            bool: 期限切れの場合True、それ以外はFalse
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
