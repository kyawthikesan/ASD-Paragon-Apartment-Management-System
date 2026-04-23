# Student Name: Nang Phwe Hleng Hun
# Student ID: 24043841
# Module: UFCF8S-30-2 Advanced Software Development

from database.db_manager import DBManager

class LocationDAO:
    @staticmethod
    def add_location(city, office_name=None):
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO locations (city, office_name)
            VALUES (?, ?)
            """,
            (city, office_name),
        )
        conn.commit()
        location_id = cursor.lastrowid
        conn.close()
        return location_id

    @staticmethod
    def get_all_locations():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT location_id, city FROM locations")
        rows = cursor.fetchall()

        conn.close()
        return rows


# Backward-compatible function aliases for older imports in tests/modules.
def add_location(city, office_name=None):
    return LocationDAO.add_location(city, office_name)
