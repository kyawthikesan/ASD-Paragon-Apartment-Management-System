--Student Name: Nang Phwe Hleng Hun
--Student ID: 24043841
--Module: UFCF8S-30-2 Advanced Software Development

PRAGMA foreign_keys = ON;

-- =========================
-- Roles Table
-- =========================
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE
);

-- =========================
-- Users Table
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    location TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login TEXT,

    FOREIGN KEY (role_id) 
        REFERENCES roles(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- =========================
-- Index for performance
-- =========================
CREATE INDEX IF NOT EXISTS idx_users_role_id 
ON users(role_id);
