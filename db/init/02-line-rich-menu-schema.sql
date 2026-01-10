-- LINE Bot チャネル設定とリッチメニュー管理のためのスキーマ定義
-- このファイルは 01-schema.sql の後に実行されることを想定しています

USE calendar_db;

-- ========================================
-- LINE Channels Table
-- ========================================
-- LINE Botのチャネル設定情報を管理
-- 複数チャネル（開発/本番など）の運用に対応

CREATE TABLE IF NOT EXISTS line_channels (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'チャネル設定の内部ID',
    channel_id VARCHAR(255) UNIQUE NOT NULL COMMENT 'LINE Developers Consoleで発行されるチャネルID',
    channel_name VARCHAR(255) NOT NULL COMMENT 'チャネルの表示名（管理用）',
    channel_access_token VARCHAR(512) NOT NULL COMMENT 'Messaging API呼び出しに必要なアクセストークン',
    channel_secret VARCHAR(255) NOT NULL COMMENT 'Webhook署名検証に必要なチャネルシークレット',
    webhook_url VARCHAR(512) NULL COMMENT 'LINEプラットフォームからのイベントを受信するエンドポイントURL',
    is_active TINYINT NOT NULL DEFAULT 1 COMMENT 'チャネルの有効/無効状態 (1: 有効, 0: 無効)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL COMMENT '更新日時',
    
    INDEX idx_channel_id (channel_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='LINE Botチャネル設定情報';


-- ========================================
-- Rich Menus Table
-- ========================================
-- LINE Botのリッチメニュー定義を管理
-- JSON形式でメニュー構造を保存し、動的な切り替えに対応

CREATE TABLE IF NOT EXISTS rich_menus (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'リッチメニュー定義の内部ID',
    rich_menu_line_id VARCHAR(255) UNIQUE NOT NULL COMMENT 'LINEプラットフォームで発行されるリッチメニューID（例: richmenu-xxxxx）',
    channel_id INT NOT NULL COMMENT 'このリッチメニューが紐づくLINEチャネルのID',
    name VARCHAR(255) NOT NULL COMMENT 'リッチメニューの内部的な識別名（例: main_menu, event_menu）',
    display_name VARCHAR(255) NULL COMMENT 'リッチメニューの表示名（管理画面用）',
    image_url VARCHAR(512) NULL COMMENT 'リッチメニュー画像のURL',
    rich_menu_json_definition JSON NOT NULL COMMENT 'リッチメニューの完全なJSON定義（size, selected, name, chatBarText, areas）',
    description TEXT NULL COMMENT 'リッチメニューの説明（管理用メモ）',
    is_active TINYINT NOT NULL DEFAULT 1 COMMENT 'リッチメニューの有効/無効状態 (1: 有効, 0: 無効)',
    is_default TINYINT NOT NULL DEFAULT 0 COMMENT 'デフォルトメニューかどうか (1: デフォルト, 0: 非デフォルト)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL COMMENT '更新日時',
    
    FOREIGN KEY (channel_id) REFERENCES line_channels(id) ON DELETE CASCADE,
    INDEX idx_rich_menu_line_id (rich_menu_line_id),
    INDEX idx_channel_id (channel_id),
    INDEX idx_name (name),
    INDEX idx_is_active (is_active),
    INDEX idx_is_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='LINE Botリッチメニュー定義';


-- ========================================
-- User Rich Menus Table
-- ========================================
-- ユーザーとリッチメニューの紐付けを管理
-- ユーザーごとに異なるメニューを表示可能にする

CREATE TABLE IF NOT EXISTS user_rich_menus (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '紐付けレコードの内部ID',
    user_id VARCHAR(255) NOT NULL COMMENT 'アプリケーションのユーザーID（通常はLINEユーザーIDを使用）',
    line_user_id VARCHAR(255) NULL COMMENT 'LINEプラットフォームのユーザーID（U-xxxxx形式）',
    rich_menu_id INT NOT NULL COMMENT 'ユーザーに紐付けられたリッチメニューのID',
    is_active TINYINT NOT NULL DEFAULT 1 COMMENT 'この紐付けの有効/無効状態 (1: 有効, 0: 無効)',
    set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT 'リッチメニューが設定された日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL COMMENT '更新日時',
    expires_at DATETIME NULL COMMENT 'リッチメニューの有効期限（NULLの場合は無期限）',
    
    FOREIGN KEY (rich_menu_id) REFERENCES rich_menus(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_line_user_id (line_user_id),
    INDEX idx_rich_menu_id (rich_menu_id),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at),
    
    -- 1ユーザーにつき1つの有効なリッチメニューのみを許可
    UNIQUE KEY uq_user_active_menu (user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='ユーザーとリッチメニューの紐付け管理';


-- ========================================
-- Sample Data (Development Only)
-- ========================================
-- 開発環境用のサンプルデータ

-- サンプルLINEチャネル（実際の値は.envから設定）
INSERT INTO line_channels (
    channel_id,
    channel_name,
    channel_access_token,
    channel_secret,
    webhook_url,
    is_active
) VALUES (
    'sample_channel_id_12345',
    'Schedule Coordinator Bot - Development',
    'sample_access_token_replace_with_real_token',
    'sample_secret_replace_with_real_secret',
    'https://your-domain.com/webhook',
    1
) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;


-- サンプルリッチメニュー定義
-- 実際のリッチメニューはLINE Messaging APIで作成後に登録
INSERT INTO rich_menus (
    rich_menu_line_id,
    channel_id,
    name,
    display_name,
    image_url,
    rich_menu_json_definition,
    description,
    is_active,
    is_default
) VALUES (
    'richmenu-sample-main-menu-001',
    1,
    'main_menu',
    'メインメニュー',
    'https://example.com/images/main_menu.png',
    JSON_OBJECT(
        'size', JSON_OBJECT('width', 2500, 'height', 1686),
        'selected', true,
        'name', 'Main Menu',
        'chatBarText', 'メニュー',
        'areas', JSON_ARRAY(
            JSON_OBJECT(
                'bounds', JSON_OBJECT('x', 0, 'y', 0, 'width', 1250, 'height', 843),
                'action', JSON_OBJECT('type', 'message', 'text', '予定を確認')
            ),
            JSON_OBJECT(
                'bounds', JSON_OBJECT('x', 1250, 'y', 0, 'width', 1250, 'height', 843),
                'action', JSON_OBJECT('type', 'message', 'text', '予定を登録')
            ),
            JSON_OBJECT(
                'bounds', JSON_OBJECT('x', 0, 'y', 843, 'width', 1250, 'height', 843),
                'action', JSON_OBJECT('type', 'message', 'text', 'カレンダー連携')
            ),
            JSON_OBJECT(
                'bounds', JSON_OBJECT('x', 1250, 'y', 843, 'width', 1250, 'height', 843),
                'action', JSON_OBJECT('type', 'message', 'text', '設定')
            )
        )
    ),
    'デフォルトのメインメニュー。予定確認、登録、カレンダー連携、設定の4つのボタンを配置。',
    1,
    1
) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;


-- ========================================
-- JSON Query Examples
-- ========================================
-- MySQLのJSON関数を使ったクエリ例

-- リッチメニューのJSON定義から特定のフィールドを抽出
-- SELECT 
--     id,
--     name,
--     JSON_EXTRACT(rich_menu_json_definition, '$.name') AS menu_name,
--     JSON_EXTRACT(rich_menu_json_definition, '$.chatBarText') AS chat_bar_text,
--     JSON_EXTRACT(rich_menu_json_definition, '$.size.width') AS menu_width,
--     JSON_EXTRACT(rich_menu_json_definition, '$.size.height') AS menu_height
-- FROM rich_menus;

-- リッチメニューのエリア数を取得
-- SELECT 
--     id,
--     name,
--     JSON_LENGTH(rich_menu_json_definition, '$.areas') AS area_count
-- FROM rich_menus;

-- 特定のアクションタイプを持つリッチメニューを検索
-- SELECT 
--     id,
--     name
-- FROM rich_menus
-- WHERE JSON_CONTAINS(
--     rich_menu_json_definition,
--     '"message"',
--     '$[*].areas[*].action.type'
-- );


-- ========================================
-- Utility Views (Optional)
-- ========================================

-- アクティブなリッチメニューとそのユーザー数を集計するビュー
CREATE OR REPLACE VIEW v_rich_menu_usage AS
SELECT 
    rm.id,
    rm.name,
    rm.display_name,
    rm.is_default,
    COUNT(urm.id) AS active_user_count,
    rm.created_at,
    rm.updated_at
FROM rich_menus rm
LEFT JOIN user_rich_menus urm ON rm.id = urm.rich_menu_id AND urm.is_active = 1
WHERE rm.is_active = 1
GROUP BY rm.id, rm.name, rm.display_name, rm.is_default, rm.created_at, rm.updated_at;


-- チャネルごとのリッチメニュー統計ビュー
CREATE OR REPLACE VIEW v_channel_menu_stats AS
SELECT 
    lc.id AS channel_id,
    lc.channel_name,
    COUNT(rm.id) AS total_menus,
    SUM(CASE WHEN rm.is_active = 1 THEN 1 ELSE 0 END) AS active_menus,
    SUM(CASE WHEN rm.is_default = 1 THEN 1 ELSE 0 END) AS default_menus
FROM line_channels lc
LEFT JOIN rich_menus rm ON lc.id = rm.channel_id
GROUP BY lc.id, lc.channel_name;


-- ========================================
-- Performance Optimization
-- ========================================
-- JSON定義内の特定フィールドへのアクセスを高速化するための Generated Column（MySQL 5.7.6+）

-- ALTER TABLE rich_menus 
-- ADD COLUMN menu_width INT GENERATED ALWAYS AS (JSON_EXTRACT(rich_menu_json_definition, '$.size.width')) STORED,
-- ADD COLUMN menu_height INT GENERATED ALWAYS AS (JSON_EXTRACT(rich_menu_json_definition, '$.size.height')) STORED,
-- ADD INDEX idx_menu_dimensions (menu_width, menu_height);

-- ALTER TABLE rich_menus
-- ADD COLUMN area_count INT GENERATED ALWAYS AS (JSON_LENGTH(rich_menu_json_definition, '$.areas')) STORED,
-- ADD INDEX idx_area_count (area_count);
