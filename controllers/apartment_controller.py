from database.database import get_connection


class ApartmentController:

    @staticmethod
    def add_apartment(city, apt_type, rent, status):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO apartments (city, type, rent, status) VALUES (?, ?, ?, ?)",
            (city, apt_type, rent, status)
        )

        conn.commit()
        conn.close()

    @staticmethod
    def get_all_apartments():

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM apartments")
        apartments = cursor.fetchall()

        conn.close()

        return apartments