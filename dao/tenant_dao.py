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
        conn.row_factory = lambda cursor, row: {
            "tenantID": row[0],
            "name": row[1],
            "NI_number": row[2],
            "phone": row[3],
            "email": row[4],
            "lease_status": row[5]
        }
        cursor = conn.cursor()

        cursor.execute("""
        SELECT 
            t.tenantID,
            t.name,
            t.NI_number,
            t.phone,
            t.email,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM leases l 
                    WHERE l.tenantID = t.tenantID 
                    AND l.status = 'Active'
                ) THEN 'Active'
                WHEN EXISTS (
                    SELECT 1 FROM leases l 
                    WHERE l.tenantID = t.tenantID
                ) THEN 'Ended'
                ELSE 'NO LEASE'
            END as lease_status
        FROM tenants t
        ORDER BY t.tenantID DESC
        """)

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

    @staticmethod
    def get_available_tenants():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT tenantID, name
        FROM tenants
        WHERE tenantID NOT IN (
            SELECT tenantID FROM leases
            WHERE status = 'Active'
        )
        """)

        rows = cursor.fetchall()
        conn.close()
        return rows