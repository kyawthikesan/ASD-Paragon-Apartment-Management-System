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

        lease_summary_sql = """
            SELECT
                tenantID,
                CASE
                    WHEN SUM(CASE WHEN LOWER(TRIM(status)) = 'active' THEN 1 ELSE 0 END) > 0
                        THEN 'Active'
                    WHEN COUNT(*) > 0
                        THEN MAX(status)
                    ELSE 'No Lease'
                END AS lease_status
            FROM leases
            GROUP BY tenantID
        """

        if city:
            cursor.execute(
                """
                SELECT
                    t.tenantID,
                    t.name,
                    t.NI_number,
                    t.phone,
                    t.email,
                    COALESCE(ls.lease_status, 'No Lease') AS lease_status
                FROM tenants t
                LEFT JOIN ({lease_summary}) ls ON t.tenantID = ls.tenantID
                WHERE EXISTS (
                    SELECT 1
                    FROM leases l
                    JOIN apartments a ON l.apartmentID = a.apartmentID
                    LEFT JOIN locations loc ON a.location_id = loc.location_id
                    WHERE l.tenantID = t.tenantID
                    AND loc.city = ?
                )
                ORDER BY t.tenantID DESC
                """.format(lease_summary=lease_summary_sql),
                (city,),
            )
        else:
            cursor.execute("""
                SELECT
                    t.tenantID,
                    t.name,
                    t.NI_number,
                    t.phone,
                    t.email,
                    COALESCE(ls.lease_status, 'No Lease') AS lease_status
                FROM tenants t
                LEFT JOIN ({lease_summary}) ls ON t.tenantID = ls.tenantID
                ORDER BY t.tenantID DESC
            """.format(lease_summary=lease_summary_sql))

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
