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
    def run_seed():
        conn = DBManager.get_connection()
        with open("database/seed.sql", "r") as file:
            conn.executescript(file.read())
        conn.commit()
        conn.close()

    @staticmethod
    def initialise_database():
        conn = DBManager.get_connection()

        conn.executescript("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE
        );

        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER NOT NULL,
            permission_key TEXT NOT NULL,
            allowed INTEGER NOT NULL DEFAULT 0 CHECK(allowed IN (0, 1)),
            PRIMARY KEY(role_id, permission_key),
            FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE
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

        CREATE TABLE IF NOT EXISTS tenants (
            tenantID INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            NI_number TEXT UNIQUE
        );

        CREATE TABLE IF NOT EXISTS locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            office_name TEXT
        );

        CREATE TABLE IF NOT EXISTS apartments (
            apartmentID INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            type TEXT,
            rent REAL,
            rooms INTEGER,
            status TEXT CHECK(status IN ('AVAILABLE','OCCUPIED')) DEFAULT 'AVAILABLE',
            FOREIGN KEY (location_id) REFERENCES locations(location_id)
        );

        CREATE TABLE IF NOT EXISTS leases (
            leaseID INTEGER PRIMARY KEY AUTOINCREMENT,
            tenantID INTEGER,
            apartmentID INTEGER,
            start_date TEXT,
            end_date TEXT,
            status TEXT,
            FOREIGN KEY(tenantID) REFERENCES tenants(tenantID),
            FOREIGN KEY(apartmentID) REFERENCES apartments(apartmentID)
        );

        CREATE TABLE IF NOT EXISTS invoices (
            invoiceID INTEGER PRIMARY KEY AUTOINCREMENT,
            leaseID INTEGER NOT NULL,
            billing_period_start TEXT NOT NULL,
            billing_period_end TEXT NOT NULL,
            due_date TEXT NOT NULL,
            amount_due REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'UNPAID'
                CHECK(status IN ('UNPAID', 'PARTIAL', 'PAID', 'LATE')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(leaseID) REFERENCES leases(leaseID)
        );

        CREATE TABLE IF NOT EXISTS payments (
            paymentID INTEGER PRIMARY KEY AUTOINCREMENT,
            invoiceID INTEGER NOT NULL,
            payment_date TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            payment_method TEXT DEFAULT 'MANUAL',
            receipt_number TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(invoiceID) REFERENCES invoices(invoiceID)
        );

        CREATE TABLE IF NOT EXISTS maintenance_requests (
            requestID INTEGER PRIMARY KEY AUTOINCREMENT,
            apartmentID INTEGER,
            tenantID INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT NOT NULL DEFAULT 'Medium',
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(apartmentID) REFERENCES apartments(apartmentID),
            FOREIGN KEY(tenantID) REFERENCES tenants(tenantID)
        );
        """)

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        user_columns = {str(row["name"]).strip().lower() for row in cursor.fetchall()}
        if "last_login" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TEXT")

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='maintenance'"
        )
        has_legacy_maintenance = cursor.fetchone() is not None
        if has_legacy_maintenance:
            cursor.execute(
                """
                INSERT INTO maintenance_requests (
                    requestID,
                    apartmentID,
                    tenantID,
                    title,
                    description,
                    priority,
                    status,
                    created_at,
                    updated_at
                )
                SELECT
                    m.requestID,
                    m.apartmentID,
                    m.tenantID,
                    COALESCE(NULLIF(TRIM(m.title), ''), 'Maintenance Request'),
                    m.description,
                    COALESCE(NULLIF(TRIM(m.priority), ''), 'Medium'),
                    COALESCE(NULLIF(TRIM(m.status), ''), 'Open'),
                    COALESCE(m.created_at, CURRENT_TIMESTAMP),
                    COALESCE(m.updated_at, COALESCE(m.created_at, CURRENT_TIMESTAMP))
                FROM maintenance m
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM maintenance_requests mr
                    WHERE mr.requestID = m.requestID
                )
                """
            )

        conn.commit()
        conn.close()
