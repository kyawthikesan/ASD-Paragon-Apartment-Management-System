import sqlite3

DB_NAME = "pams.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ni_number TEXT UNIQUE,
        phone TEXT,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apartments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        type TEXT NOT NULL,
        rent REAL NOT NULL,
        status TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        apartment_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        FOREIGN KEY(tenant_id) REFERENCES tenants(id),
        FOREIGN KEY(apartment_id) REFERENCES apartments(id)
    )
    """)

    conn.commit()
    conn.close()


def seed_default_users():
    """
    Creates 5 demo accounts (one per role) if they don't already exist.
    """
    users_to_seed = [
        ("admin", "admin123", "Administrator"),
        ("frontdesk1", "fd123", "Front-desk Staff"),
        ("finance1", "fin123", "Finance Manager"),
        ("maint1", "mt123", "Maintenance Staff"),
        ("manager1", "mgr123", "Manager"),
    ]

    conn = get_connection()
    cursor = conn.cursor()

    for username, password, role in users_to_seed:
        cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )

    conn.commit()
    conn.close()