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
    def get_all_apartments(city=None):
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        query = """
        SELECT 
            a.apartmentID,
            l.city,
            a.type,
            a.rent,
            a.rooms,
            a.status
        FROM apartments a
        JOIN locations l ON a.location_id = l.location_id
        """
        params = []
        if city:
            query += " WHERE l.city = ?"
            params.append(city)
        query += " ORDER BY a.apartmentID DESC"
        cursor.execute(query, tuple(params))
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
    def search_apartment(keyword, city=None):
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        query = """
        SELECT 
            a.apartmentID,
            l.city,
            a.type,
            a.rent,
            a.rooms,
            a.status
        FROM apartments a
        JOIN locations l ON a.location_id = l.location_id
        WHERE a.type LIKE ?
        """
        params = [f"%{keyword}%"]
        if city:
            query += " AND l.city = ?"
            params.append(city)
        query += " ORDER BY a.apartmentID DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_available_apartments(city=None):
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        query = """
        SELECT 
            a.apartmentID,
            l.city,
            a.type
        FROM apartments a
        JOIN locations l ON a.location_id = l.location_id
        WHERE UPPER(a.status) = 'AVAILABLE'
        """
        params = []
        if city:
            query += " AND l.city = ?"
            params.append(city)
        cursor.execute(query, tuple(params))

        rows = cursor.fetchall()
        conn.close()
        return rows


# Backward-compatible function alias for older imports in tests/modules.
def add_apartment(location_id, apartment_type, rent, rooms):
    ApartmentDAO.add_apartment(location_id, apartment_type, rent, rooms)
