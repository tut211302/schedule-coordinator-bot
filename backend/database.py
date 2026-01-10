"""
Database Configuration and Session Management
SQLAlchemyのセットアップとデータベース接続管理
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+mysqlconnector://devuser:devpass123@db:3306/calendar_db"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 接続の有効性を確認
    pool_recycle=3600,   # 1時間ごとに接続をリサイクル
    echo=False,          # SQLログを出力しない（開発時はTrueに設定可能）
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    データベースセッションを取得する依存性注入用の関数
    
    FastAPIのDependsで使用:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: SQLAlchemyのデータベースセッション
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    データベースの初期化
    すべてのモデルのテーブルを作成します
    
    注意: 本番環境ではAlembicなどのマイグレーションツールを使用してください
    """
    from models import line_channel, rich_menu, user_rich_menu
    
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def check_db_connection() -> bool:
    """
    データベース接続をテストする
    
    Returns:
        bool: 接続が成功した場合True、失敗した場合False
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
