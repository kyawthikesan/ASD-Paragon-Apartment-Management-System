from database.db_manager import DBManager

class TenantDAO:

    @staticmethod
    def add_tenant(name, NI_number, phone, email):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO tenants (name, NI_number, phone, email)
        VALUES (?, ?, ?, ?)
        """, (name, NI_number, phone, email))

        conn.commit()
        conn.close()

    @staticmethod
    def get_all_tenants():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tenants ORDER BY tenantID DESC")
        rows = cursor.fetchall()

        conn.close()
        return rows

    @staticmethod
    def update_tenant(tenant_id, name, NI_number, phone, email):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE tenants
        SET name=?, NI_number=?, phone=?, email=?
        WHERE tenantID=?
        """, (name, NI_number, phone, email, tenant_id))

        conn.commit()
        conn.close()

    @staticmethod
    def delete_tenant(tenant_id):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tenants WHERE tenantID=?", (tenant_id,))

        conn.commit()
        conn.close()