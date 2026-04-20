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


        """)

        conn.commit()
        conn.close()