from database.db_manager import DBManager

class LocationDAO:

    @staticmethod
    def get_all_locations():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT location_id, city FROM locations")
        rows = cursor.fetchall()

        conn.close()
        return rows