from database.database import get_connection


class LoginController:

    @staticmethod
    def authenticate(username, password):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]

        return None