import sqlite3

DB_NAME = "pams.db"


class DBManager:

    @staticmethod
    def get_connection():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def initialise_database():
        conn = DBManager.get_connection()

        conn.executescript("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role_id INTEGER,
            location TEXT,
            is_active INTEGER,
            created_at TEXT,
            FOREIGN KEY(role_id) REFERENCES roles(id)
        );
        """)

        conn.commit()
        conn.close()