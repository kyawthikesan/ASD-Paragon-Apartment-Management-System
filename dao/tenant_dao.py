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
    def get_all_tenants(city=None):
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

        if city:
            cursor.execute(
                """
                SELECT DISTINCT
                    t.tenantID,
                    t.name,
                    t.NI_number,
                    t.phone,
                    t.email
                FROM tenants t
                JOIN leases l ON t.tenantID = l.tenantID
                JOIN apartments a ON l.apartmentID = a.apartmentID
                LEFT JOIN locations loc ON a.location_id = loc.location_id
                WHERE loc.city = ?
                ORDER BY t.tenantID DESC
                """,
                (city,),
            )
        else:
            cursor.execute("""
            SELECT tenantID, name, NI_number, phone, email 
            FROM tenants
            ORDER BY tenantID DESC
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
