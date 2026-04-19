from database.db_manager import DBManager


class ApartmentDAO:

    @staticmethod
    def add_apartment(location_id, type, rent, rooms):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO apartments (location_id, type, rent, rooms, status)
        VALUES (?, ?, ?, ?, ?)
        """, (location_id, type, rent, rooms, "Available"))

        conn.commit()
        conn.close()

    @staticmethod
    def get_all_apartments():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT 
            a.apartmentID,
            l.city,
            a.type,
            a.rent,
            a.rooms
        FROM apartments a
        JOIN locations l ON a.location_id = l.location_id
        ORDER BY a.apartmentID DESC
        """)
        rows = cursor.fetchall()

        conn.close()
        return rows

    @staticmethod
    def update_apartment(apartmentID, location_id, type, rent, rooms):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE apartments
        SET location_id=?, type=?, rent=?, rooms=?
        WHERE apartmentID=?
        """, (location_id, type, rent, rooms, apartmentID))

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
        SELECT 
            a.apartmentID,
            l.city,
            a.type,
            a.rent,
            a.rooms
        FROM apartments a
        JOIN locations l ON a.location_id = l.location_id
        WHERE a.type LIKE ?
        ORDER BY a.apartmentID DESC
        """, (f"%{keyword}%",))

    @staticmethod
    def get_available_apartments():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT 
            a.apartmentID,
            l.city,
            a.type
        FROM apartments a
        JOIN locations l ON a.location_id = l.location_id
        WHERE a.status = 'Available'
        """)

        rows = cursor.fetchall()
        conn.close()
        return rows