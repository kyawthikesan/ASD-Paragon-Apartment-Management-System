from database.database import get_connection


class TenantController:

    @staticmethod
    def add_tenant(name, ni, phone, email):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO tenants (name, ni_number, phone, email) VALUES (?, ?, ?, ?)",
            (name, ni, phone, email)
        )

        conn.commit()
        conn.close()

    @staticmethod
    def get_all_tenants():

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tenants")
        tenants = cursor.fetchall()

        conn.close()

        return tenants