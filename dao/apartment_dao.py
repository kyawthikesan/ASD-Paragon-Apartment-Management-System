from database.db_manager import DBManager


class ApartmentDAO:

    @staticmethod
    def add_apartment(locationID, type, rent, rooms):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO apartments (locationID, type, rent, rooms, status)
        VALUES (?, ?, ?, ?, ?)
        """, (locationID, type, rent, rooms, "Available"))

        conn.commit()
        conn.close()

    @staticmethod
    def get_all_apartments():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM apartments ORDER BY apartmentID DESC")
        rows = cursor.fetchall()

        conn.close()
        return rows

    @staticmethod
    def update_apartment(apartmentID, locationID, type, rent, rooms):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE apartments
        SET locationID=?, type=?, rent=?, rooms=?
        WHERE apartmentID=?
        """, (locationID, type, rent, rooms, apartmentID))

        conn.commit()
        conn.close()

    @staticmethod
    def delete_apartment(apartmentID):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM apartments WHERE apartmentID=?", (apartmentID,))

        conn.commit()
        conn.close()

    @staticmethod
    def search_apartment(keyword):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM apartments
        WHERE type LIKE ?
        """, (f"%{keyword}%",))

        rows = cursor.fetchall()
        conn.close()
        return rows