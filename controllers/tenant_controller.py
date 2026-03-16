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

        cursor.execute("SELECT * FROM tenants order by id DESC")
        tenants = cursor.fetchall()

        conn.close()

        return tenants
    
    @staticmethod
    def update_tenant(tenant_id, name, ni, phone, email):

        ni = ni.upper()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tenants
            SET name=?, ni_number=?, phone=?, email=?
            WHERE id=?
        """, (name, ni, phone, email, tenant_id))

        conn.commit()
        conn.close()

    @staticmethod
    def delete_tenant(tenant_id):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))

        conn.commit()
        conn.close()

    @staticmethod
    def search_tenant(keyword):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM tenants
            WHERE name LIKE ? OR ni_number LIKE ?
            """,
            (f"%{keyword}%", f"%{keyword}%")
        )

        tenants = cursor.fetchall()

        conn.close()

        return tenants