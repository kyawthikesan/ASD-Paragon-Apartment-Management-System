import sqlite3

def seed_database():
    conn = sqlite3.connect("system.db")
    cursor = conn.cursor()

    # 1. Clear existing data to avoid duplicates during testing
    cursor.execute("DELETE FROM maintenance_requests")
    
    # 2. Add sample data
    # Format: (complaint_id, staff_name, scheduled_date, status, cost, hours_spent)
    sample_data = [
        (101, "Alice Smith", "2026-04-22", "In Progress", 150.00, 3),
        (102, "Bob Jones", "2026-04-23", "Pending", 0.00, 0),
        (103, "Charlie Davis", "2026-04-21", "Resolved", 450.50, 8)
    ]

    cursor.executemany("""
        INSERT INTO maintenance_requests (complaint_id, staff_name, scheduled_date, status, cost, hours_spent)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_data)

    conn.commit()
    conn.close()
    print("Database seeded with sample maintenance records!")

if __name__ == "__main__":
    seed_database()