-- Database initialization script
-- This file is automatically executed when the MySQL container starts

USE calendar_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    line_user_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    google_id VARCHAR(255) UNIQUE,
    access_token TEXT,
    refresh_token TEXT,
    token_expiry DATETIME,
    calendar_connected BOOLEAN DEFAULT FALSE,
    display_name VARCHAR(255),
    picture_url VARCHAR(512),
    status_message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_line_user_id (line_user_id),
    INDEX idx_email (email),
    INDEX idx_google_id (google_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Calendar events table
CREATE TABLE IF NOT EXISTS calendar_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    google_event_id VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    location VARCHAR(255),
    synced BOOLEAN DEFAULT FALSE,
    last_sync DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_google_event_id (google_event_id),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sync logs table
CREATE TABLE IF NOT EXISTS sync_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    sync_type VARCHAR(50),
    status VARCHAR(50),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- OAuth state table (for CSRF protection)
CREATE TABLE IF NOT EXISTS oauth_states (
    id INT PRIMARY KEY AUTO_INCREMENT,
    state VARCHAR(255) UNIQUE NOT NULL,
    user_session_id VARCHAR(255),
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_state (state),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- LINE users table
CREATE TABLE IF NOT EXISTS line_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    line_user_id VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    picture_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_line_user_id (line_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- LINE <-> Google account link
CREATE TABLE IF NOT EXISTS line_user_links (
    id INT PRIMARY KEY AUTO_INCREMENT,
    line_user_id VARCHAR(64) NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_line_user (line_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_line_user_id (line_user_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Poll sessions per group
CREATE TABLE IF NOT EXISTS poll_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id VARCHAR(64) NOT NULL,
    topic VARCHAR(255),
    state VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_by_line_user_id VARCHAR(64),
    settings_json JSON,
    event_registered BOOLEAN DEFAULT FALSE,
    finalized_date VARCHAR(255),
    finalized_start_time TIME,
    finalized_end_time TIME,
    finalized_location VARCHAR(255),
    restaurant_id VARCHAR(255),
    restaurant_name VARCHAR(255),
    restaurant_url TEXT,
    reservation_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_group_id (group_id),
    INDEX idx_state (state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Poll options (candidate date-times)
CREATE TABLE IF NOT EXISTS poll_options (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    label VARCHAR(255),
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    created_by_line_user_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES poll_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Poll votes (one vote per user per session)
CREATE TABLE IF NOT EXISTS poll_votes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    option_id INT NOT NULL,
    line_user_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_vote_per_session_user (session_id, line_user_id),
    FOREIGN KEY (session_id) REFERENCES poll_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES poll_options(id) ON DELETE CASCADE,
    INDEX idx_option_id (option_id),
    INDEX idx_line_user_id (line_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Poll responses table (for storing user's selected dates)
-- This table stores individual date selections from the voting UI
CREATE TABLE IF NOT EXISTS poll_responses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    line_user_id VARCHAR(64) NOT NULL,
    session_id INT,
    selected_date VARCHAR(255) NOT NULL,
    start_time DATETIME,
    end_time DATETIME,
    is_late BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_line_user_id (line_user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_selected_date (selected_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Restaurant search conditions (user preferences for Hotpepper API)
CREATE TABLE IF NOT EXISTS restaurant_conditions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    line_user_id VARCHAR(64) NOT NULL,
    session_id INT,
    area VARCHAR(255),
    genre_codes JSON,
    budget_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_user_session (line_user_id, session_id),
    INDEX idx_line_user_id (line_user_id),
    INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample data (development only)
INSERT INTO users (email, calendar_connected) VALUES
('test@example.com', FALSE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Create indexes for better query performance
CREATE INDEX idx_user_calendar_status ON users(calendar_connected);
CREATE INDEX idx_sync_status ON calendar_events(synced);
