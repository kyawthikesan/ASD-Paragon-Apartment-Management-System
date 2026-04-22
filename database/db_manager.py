import sqlite3

DB_NAME = "pams.db"


class DBManager:
    @staticmethod
    def get_connection():
        """
        Create and return a SQLite connection for the application.
        Also enables useful SQLite settings for reliability and better performance.
        """
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row

        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")

        return conn

    @staticmethod
    def run_seed():
        """
        Run the SQL seed file to insert sample/mock data.
        """
        conn = DBManager.get_connection()
        with open("database/seed.sql", "r", encoding="utf-8") as file:
            conn.executescript(file.read())
        conn.commit()
        conn.close()

    @staticmethod
    def _add_column_if_missing(cursor, table_name, column_name, column_sql):
        """
        Add a column to an existing table only if it does not already exist.
        """
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = {str(row["name"]).strip().lower() for row in cursor.fetchall()}
        if column_name.lower() not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")

    @staticmethod
    def initialise_database():
        """
        Create all tables if they do not already exist,
        apply lightweight schema upgrades,
        and create indexes to improve performance.
        """
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
            scheduled_date TEXT,
            scheduled_time TEXT,
            assigned_staff TEXT,
            resolution_note TEXT,
            hours_spent REAL NOT NULL DEFAULT 0,
            cost REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(apartmentID) REFERENCES apartments(apartmentID),
            FOREIGN KEY(tenantID) REFERENCES tenants(tenantID)
        );

        -- =========================
        -- Indexes for performance
        -- =========================

        CREATE INDEX IF NOT EXISTS idx_users_role_id
        ON users(role_id);

        CREATE INDEX IF NOT EXISTS idx_users_location
        ON users(location);

        CREATE INDEX IF NOT EXISTS idx_locations_city
        ON locations(city);

        CREATE INDEX IF NOT EXISTS idx_apartments_location_id
        ON apartments(location_id);

        CREATE INDEX IF NOT EXISTS idx_apartments_location_status
        ON apartments(location_id, status);

        CREATE INDEX IF NOT EXISTS idx_apartments_status
        ON apartments(status);

        CREATE INDEX IF NOT EXISTS idx_leases_tenant
        ON leases(tenantID);

        CREATE INDEX IF NOT EXISTS idx_leases_apartment
        ON leases(apartmentID);

        CREATE INDEX IF NOT EXISTS idx_leases_status
        ON leases(status);

        CREATE INDEX IF NOT EXISTS idx_leases_end_date
        ON leases(end_date);

        CREATE INDEX IF NOT EXISTS idx_leases_apartment_status_end
        ON leases(apartmentID, status, end_date);

        CREATE INDEX IF NOT EXISTS idx_invoices_lease
        ON invoices(leaseID);

        CREATE INDEX IF NOT EXISTS idx_invoices_status
        ON invoices(status);

        CREATE INDEX IF NOT EXISTS idx_invoices_due_date
        ON invoices(due_date);

        CREATE INDEX IF NOT EXISTS idx_invoices_lease_status_due
        ON invoices(leaseID, status, due_date);

        CREATE INDEX IF NOT EXISTS idx_payments_invoice
        ON payments(invoiceID);

        CREATE INDEX IF NOT EXISTS idx_payments_payment_date
        ON payments(payment_date);

        CREATE INDEX IF NOT EXISTS idx_payments_created_at
        ON payments(created_at);

        CREATE INDEX IF NOT EXISTS idx_payments_invoice_date
        ON payments(invoiceID, payment_date);

        CREATE INDEX IF NOT EXISTS idx_maintenance_apartment
        ON maintenance_requests(apartmentID);

        CREATE INDEX IF NOT EXISTS idx_maintenance_tenant
        ON maintenance_requests(tenantID);

        CREATE INDEX IF NOT EXISTS idx_maintenance_status
        ON maintenance_requests(status);

        CREATE INDEX IF NOT EXISTS idx_maintenance_priority
        ON maintenance_requests(priority);

        CREATE INDEX IF NOT EXISTS idx_maintenance_status_priority
        ON maintenance_requests(status, priority);

        CREATE INDEX IF NOT EXISTS idx_maintenance_created_at
        ON maintenance_requests(created_at);

        CREATE INDEX IF NOT EXISTS idx_maintenance_scheduled_date
        ON maintenance_requests(scheduled_date);

        CREATE INDEX IF NOT EXISTS idx_maintenance_assigned_staff
        ON maintenance_requests(assigned_staff);
        """)

        cursor = conn.cursor()

        # =========================
        # Lightweight schema upgrades
        # =========================

        DBManager._add_column_if_missing(
            cursor,
            "users",
            "last_login",
            "last_login TEXT"
        )

        DBManager._add_column_if_missing(
            cursor,
            "maintenance_requests",
            "scheduled_date",
            "scheduled_date TEXT"
        )
        DBManager._add_column_if_missing(
            cursor,
            "maintenance_requests",
            "scheduled_time",
            "scheduled_time TEXT"
        )
        DBManager._add_column_if_missing(
            cursor,
            "maintenance_requests",
            "assigned_staff",
            "assigned_staff TEXT"
        )
        DBManager._add_column_if_missing(
            cursor,
            "maintenance_requests",
            "resolution_note",
            "resolution_note TEXT"
        )
        DBManager._add_column_if_missing(
            cursor,
            "maintenance_requests",
            "hours_spent",
            "hours_spent REAL NOT NULL DEFAULT 0"
        )
        DBManager._add_column_if_missing(
            cursor,
            "maintenance_requests",
            "cost",
            "cost REAL NOT NULL DEFAULT 0"
        )

        # =========================
        # Legacy maintenance table migration
        # If an older table named "maintenance" exists,
        # copy its rows into the new maintenance_requests table
        # =========================
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='maintenance'"
        )
        has_legacy_maintenance = cursor.fetchone() is not None

        if has_legacy_maintenance:
            cursor.execute("PRAGMA table_info(maintenance)")
            legacy_columns = {str(row["name"]).strip().lower() for row in cursor.fetchall()}

            has_request_id = "requestid" in legacy_columns
            has_apartment_id = "apartmentid" in legacy_columns
            has_tenant_id = "tenantid" in legacy_columns
            has_title = "title" in legacy_columns
            has_description = "description" in legacy_columns
            has_priority = "priority" in legacy_columns
            has_status = "status" in legacy_columns
            has_scheduled_date = "scheduled_date" in legacy_columns
            has_staff_name = "staff_name" in legacy_columns
            has_hours_spent = "hours_spent" in legacy_columns
            has_cost = "cost" in legacy_columns
            has_created_at = "created_at" in legacy_columns
            has_updated_at = "updated_at" in legacy_columns
            if has_request_id:
                cursor.execute(f"""
                    INSERT INTO maintenance_requests (
                        requestID,
                        apartmentID,
                        tenantID,
                        title,
                        description,
                        priority,
                        status,
                        scheduled_date,
                        assigned_staff,
                        hours_spent,
                        cost,
                        created_at,
                        updated_at
                    )
                    SELECT
                        m.requestID,
                        {"m.apartmentID" if has_apartment_id else "NULL"},
                        {"m.tenantID" if has_tenant_id else "NULL"},
                        {("COALESCE(NULLIF(TRIM(m.title), ''), 'Maintenance Request')") if has_title else "'Maintenance Request'"},
                        {"m.description" if has_description else "NULL"},
                        {("COALESCE(NULLIF(TRIM(m.priority), ''), 'Medium')") if has_priority else "'Medium'"},
                        {("COALESCE(NULLIF(TRIM(m.status), ''), 'Open')") if has_status else "'Open'"},
                        {"m.scheduled_date" if has_scheduled_date else "NULL"},
                        {"m.staff_name" if has_staff_name else "NULL"},
                        {"COALESCE(m.hours_spent, 0)" if has_hours_spent else "0"},
                        {"COALESCE(m.cost, 0)" if has_cost else "0"},
                        {"COALESCE(m.created_at, CURRENT_TIMESTAMP)" if has_created_at else "CURRENT_TIMESTAMP"},
                        {"COALESCE(m.updated_at, COALESCE(m.created_at, CURRENT_TIMESTAMP))" if has_updated_at and has_created_at else ("COALESCE(m.updated_at, CURRENT_TIMESTAMP)" if has_updated_at else ("COALESCE(m.created_at, CURRENT_TIMESTAMP)" if has_created_at else "CURRENT_TIMESTAMP"))}
                    FROM maintenance m
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM maintenance_requests mr
                        WHERE mr.requestID = m.requestID
                    )
                """)
            else:
                cursor.execute(f"""
                    INSERT INTO maintenance_requests (
                        apartmentID,
                        tenantID,
                        title,
                        description,
                        priority,
                        status,
                        scheduled_date,
                        assigned_staff,
                        hours_spent,
                        cost,
                        created_at,
                        updated_at
                    )
                    SELECT
                        {"m.apartmentID" if has_apartment_id else "NULL"},
                        {"m.tenantID" if has_tenant_id else "NULL"},
                        {("COALESCE(NULLIF(TRIM(m.title), ''), 'Maintenance Request')") if has_title else "'Maintenance Request'"},
                        {"m.description" if has_description else "NULL"},
                        {("COALESCE(NULLIF(TRIM(m.priority), ''), 'Medium')") if has_priority else "'Medium'"},
                        {("COALESCE(NULLIF(TRIM(m.status), ''), 'Open')") if has_status else "'Open'"},
                        {"m.scheduled_date" if has_scheduled_date else "NULL"},
                        {"m.staff_name" if has_staff_name else "NULL"},
                        {"COALESCE(m.hours_spent, 0)" if has_hours_spent else "0"},
                        {"COALESCE(m.cost, 0)" if has_cost else "0"},
                        {"COALESCE(m.created_at, CURRENT_TIMESTAMP)" if has_created_at else "CURRENT_TIMESTAMP"},
                        {"COALESCE(m.updated_at, COALESCE(m.created_at, CURRENT_TIMESTAMP))" if has_updated_at and has_created_at else ("COALESCE(m.updated_at, CURRENT_TIMESTAMP)" if has_updated_at else ("COALESCE(m.created_at, CURRENT_TIMESTAMP)" if has_created_at else "CURRENT_TIMESTAMP"))}
                    FROM maintenance m
                """)

        conn.commit()
        conn.close()