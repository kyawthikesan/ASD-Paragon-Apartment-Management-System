import sqlite3
import os

class MaintenanceDAO:
    def __init__(self):
        # 1. This finds the absolute path of the folder where THIS script is saved 
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_dir, "system.db")
        
        # 2. Connect using the absolute path
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # Table for complaints 
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    status TEXT DEFAULT 'Open'
                )
            """)
            # Table for maintenance requests [cite: 62, 66]
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complaint_id INTEGER,
                    staff_name TEXT,
                    scheduled_date TEXT,
                    status TEXT DEFAULT 'Pending',
                    cost REAL DEFAULT 0.0,
                    hours_spent INTEGER DEFAULT 0,
                    FOREIGN KEY (complaint_id) REFERENCES complaints (id)
                )
            """)

    def log_request(self, complaint_id):
        with self.conn:
            self.conn.execute("INSERT INTO maintenance_requests (complaint_id) VALUES (?)", (complaint_id,))

    def update_maintenance(self, req_id, staff, date, status, cost, hours):
        query = "UPDATE maintenance_requests SET staff_name=?, scheduled_date=?, status=?, cost=?, hours_spent=? WHERE id=?"
        with self.conn:
            self.conn.execute(query, (staff, date, status, cost, hours, req_id))

    def get_all_requests(self):
        cursor = self.conn.execute("SELECT * FROM maintenance_requests")
        return cursor.fetchall()

    def get_cost_report_data(self):
        # Generates a report on costs and hours 
        cursor = self.conn.execute("SELECT SUM(cost), SUM(hours_spent), COUNT(id) FROM maintenance_requests WHERE status='Resolved'")
        return cursor.fetchone()

# --- Verification Logic ---
if __name__ == "__main__":
    dao = MaintenanceDAO()
    if os.path.exists(dao.db_path):
        print(f"system.db created successfully at: {dao.db_path}")
    else:
        print("Error: Database file still not found.")