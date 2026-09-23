
-- ====================================================================
-- 1. SESSIONS TABLE
-- Manages the stateful browsing windows grouped by timestamps.
-- ====================================================================
-- CREATE TABLE IF NOT EXISTS sessions (
-- session_id TEXT PRIMARY KEY,
-- created_at TEXT NOT NULL,
-- last_active TEXT NOT NULL,
-- is_active INTEGER NOT NULL DEFAULT 1 -- 1 = Tracking Active, 0 = Inactive/Closed Session
-- ); 

-- ====================================================================
-- 2. TABS TABLE
-- Logs individual webpage metadata. Includes relational safety keys
-- and unique composite configurations required for instant Upsert operations.
-- ====================================================================
-- CREATE TABLE IF NOT EXISTS tabs (
-- id INTEGER PRIMARY KEY AUTOINCREMENT,
-- session_id TEXT NOT NULL,
-- url TEXT NOT NULL,
-- title TEXT,
-- fav_icon_url TEXT,
-- visit_count INTEGER NOT NULL DEFAULT 1,
-- first_visited TEXT NOT NULL,
-- last_visited TEXT NOT NULL,
-- -- Cascading constraint: If a parent session is deleted, flush all child logs automatically
-- FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
-- -- Composite unique rule: Ensures a single URL can only appear ONCE per active session timeline
-- UNIQUE (session_id, url)
-- ); 

-- ====================================================================
-- 3. PERFORMANCE LOOKUP INDEXES
-- Optimizes query fetch response times for the frontend Extension Popup panel.
-- ====================================================================
-- CREATE INDEX IF NOT EXISTS idx_tabs_session ON tabs (session_id);
-- CREATE INDEX IF NOT EXISTS idx_tabs_last_visited ON tabs (last_visited);




-- ====================================================================
-- 1. ENFORCEMENT
-- Required to make the ON DELETE CASCADE actually work in SQLite
-- ====================================================================
PRAGMA foreign_keys = ON;

-- ====================================================================
-- 2. SESSIONS TABLE
-- Manages the stateful browsing windows grouped by timestamps.
-- ====================================================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    last_active TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 -- 1 = Tracking Active, 0 = Inactive/Closed Session
);

-- ====================================================================
-- 3. TABS TABLE
-- Logs individual webpage metadata. Includes relational safety keys
-- and unique composite configurations required for instant Upsert operations.
-- ====================================================================
CREATE TABLE IF NOT EXISTS tabs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    fav_icon_url TEXT,
    visit_count INTEGER NOT NULL DEFAULT 1,
    first_visited TEXT NOT NULL,
    last_visited TEXT NOT NULL,
    -- Cascading constraint: If a parent session is deleted, flush all child logs automatically
    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
    -- Composite unique rule: Ensures a single URL can only appear ONCE per active session timeline
    UNIQUE (session_id, url)
);

-- ====================================================================
-- 4. PERFORMANCE LOOKUP INDEXES
-- Optimizes query fetch response times for the frontend Extension Popup panel.
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_tabs_session ON tabs (session_id);
CREATE INDEX IF NOT EXISTS idx_tabs_last_visited ON tabs (last_visited);