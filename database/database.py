import sqlite3

DB_NAME = "pams.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        ni_number TEXT,
        phone TEXT,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apartments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        type TEXT,
        rent REAL,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER,
        apartment_id INTEGER,
        start_date TEXT,
        end_date TEXT
    )
    """)

    conn.commit()
    conn.close()


def seed_admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username,password,role) VALUES (?,?,?)",
            ("admin", "admin123", "Administrator")
        )

    conn.commit()
    conn.close()