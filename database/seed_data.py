# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

import sqlite3


def seed_database():
    conn = sqlite3.connect("pams.db")
    cursor = conn.cursor()

    # Clear existing maintenance data for testing
    cursor.execute("DELETE FROM maintenance_requests")

    sample_data = [
        (
            1,                  # apartmentID
            1,                  # tenantID
            "Leaking sink",
            "Kitchen sink is leaking under the cabinet.",
            "High",
            "In Progress",
            "2026-04-22",
            "10:00",
            "Alice Smith",
            "",
            0.0,
            0.0
        ),
        (
            2,
            2,
            "Broken heater",
            "Bedroom heater is not working.",
            "Medium",
            "Scheduled",
            "2026-04-23",
            "14:30",
            "Bob Jones",
            "",
            0.0,
            0.0
        ),
        (
            3,
            3,
            "Window lock issue",
            "Living room window lock is jammed.",
            "Low",
            "Resolved",
            "2026-04-21",
            "09:00",
            "Charlie Davis",
            "Lock repaired and tested.",
            2.5,
            85.50
        )
    ]

    cursor.executemany("""
        INSERT INTO maintenance_requests (
            apartmentID,
            tenantID,
            title,
            description,
            priority,
            status,
            scheduled_date,
            scheduled_time,
            assigned_staff,
            resolution_note,
            hours_spent,
            cost
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_data)

    conn.commit()
    conn.close()
    print("Database seeded with sample maintenance records!")


if __name__ == "__main__":
    seed_database()