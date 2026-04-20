from database.db_manager import DBManager

class LoginController:
    @staticmethod
    def authenticate(username, password):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, role FROM users WHERE username=? AND password=?",
            (username, password)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {"user_id": row[0], "role": row[1]}
        return None