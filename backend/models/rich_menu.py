"""
Rich Menu Model
管理LINE Botのリッチメニュー定義情報
"""

from datetime import datetime
from typing import Optional, Dict, Any
import json

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text, func
from sqlalchemy.orm import relationship

from database import Base


class RichMenu(Base):
    """
    リッチメニューモデル
    
    LINE Messaging APIのリッチメニュー定義を管理します。
    リッチメニューID、表示設定、アクション定義などをデータベースで管理することで、
    動的なメニュー切り替えや、バージョン管理が可能になります。
    """
    __tablename__ = 'rich_menus'

    # Primary Key
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
        comment='リッチメニュー定義の内部ID'
    )
    
    # LINE Platform Information
    rich_menu_line_id = Column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True,
        comment='LINEプラットフォームで発行されるリッチメニューID（例: richmenu-xxxxx）'
    )
    
    # Foreign Key to LineChannel
    channel_id = Column(
        Integer, 
        ForeignKey('line_channels.id', ondelete='CASCADE'), 
        nullable=False,
        index=True,
        comment='このリッチメニューが紐づくLINEチャネルのID'
    )
    
    # Menu Identification
    name = Column(
        String(255), 
        nullable=False,
        index=True,
        comment='リッチメニューの内部的な識別名（例: main_menu, event_menu）'
    )
    
    display_name = Column(
        String(255), 
        nullable=True,
        comment='リッチメニューの表示名（管理画面用、ユーザーには表示されない）'
    )
    
    # Menu Assets
    image_url = Column(
        String(512), 
        nullable=True,
        comment='リッチメニュー画像のURL（LINEにアップロードした画像のURL）'
    )
    
    # Rich Menu Definition (JSON)
    rich_menu_json_definition = Column(
        JSON,
        nullable=False,
        comment='リッチメニューの完全なJSON定義（size, selected, name, chatBarText, areas）'
    )
    
    # Menu Description
    description = Column(
        Text,
        nullable=True,
        comment='リッチメニューの説明（管理用メモ）'
    )
    
    # Status
    is_active = Column(
        Integer,
        default=1,
        nullable=False,
        comment='リッチメニューの有効/無効状態 (1: 有効, 0: 無効)'
    )
    
    is_default = Column(
        Integer,
        default=0,
        nullable=False,
        comment='デフォルトメニューかどうか (1: デフォルト, 0: 非デフォルト)'
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
    channel = relationship(
        'LineChannel',
        back_populates='rich_menus'
    )
    
    user_rich_menus = relationship(
        'UserRichMenu',
        back_populates='rich_menu',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        """モデルの文字列表現"""
        return (
            f"<RichMenu("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"rich_menu_line_id='{self.rich_menu_line_id}', "
            f"channel_id={self.channel_id}, "
            f"is_active={self.is_active}"
            f")>"
        )
    
    def to_dict(self, include_definition: bool = False) -> dict:
        """
        モデルを辞書形式に変換（API レスポンス用）
        
        Args:
            include_definition: JSON定義を含めるかどうか
        
        Returns:
            dict: モデルの辞書表現
        """
        result = {
            'id': self.id,
            'rich_menu_line_id': self.rich_menu_line_id,
            'channel_id': self.channel_id,
            'name': self.name,
            'display_name': self.display_name,
            'image_url': self.image_url,
            'description': self.description,
            'is_active': bool(self.is_active),
            'is_default': bool(self.is_default),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_definition:
            result['rich_menu_json_definition'] = self.rich_menu_json_definition
        
        return result
    
    def get_menu_areas(self) -> list:
        """
        リッチメニューのエリア定義を取得
        
        Returns:
            list: areas配列（JSON定義内のareasフィールド）
        """
        if self.rich_menu_json_definition and 'areas' in self.rich_menu_json_definition:
            return self.rich_menu_json_definition['areas']
        return []
    
    def get_menu_size(self) -> dict:
        """
        リッチメニューのサイズ情報を取得
        
        Returns:
            dict: サイズ情報（width, height）
        """
        if self.rich_menu_json_definition and 'size' in self.rich_menu_json_definition:
            return self.rich_menu_json_definition['size']
        return {'width': 0, 'height': 0}
