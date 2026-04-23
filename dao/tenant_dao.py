# Student Name: Nang Phwe Hleng Hun
# Student ID: 24043841
# Module: UFCF8S-30-2 Advanced Software Development

from database.db_manager import DBManager


class TenantDAO:

    @staticmethod
    def add_tenant(name, NI_number, phone, email):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT INTO tenants (name, NI_number, phone, email)
        VALUES (?, ?, ?, ?)
        """,
            (name, NI_number, phone, email),
        )

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
            "lease_status": row[5],
            "apartmentID": row[6],
            "apartment_type": row[7],
            "city": row[8],
            "start_date": row[9],
            "end_date": row[10],
            "rent": row[11],
        }
        cursor = conn.cursor()

        query = """
            SELECT
                t.tenantID,
                t.name,
                t.NI_number,
                t.phone,
                t.email,
                COALESCE(
                    CASE
                        WHEN LOWER(TRIM(l.status)) = 'active' THEN 'Active'
                        WHEN TRIM(COALESCE(l.status, '')) = '' THEN 'No Lease'
                        ELSE l.status
                    END,
                    'No Lease'
                ) AS lease_status,
                a.apartmentID,
                a.type,
                loc.city,
                l.start_date,
                l.end_date,
                a.rent
            FROM tenants t
            LEFT JOIN leases l
                ON l.leaseID = (
                    SELECT l2.leaseID
                    FROM leases l2
                    LEFT JOIN apartments a2 ON l2.apartmentID = a2.apartmentID
                    LEFT JOIN locations loc2 ON a2.location_id = loc2.location_id
                    WHERE l2.tenantID = t.tenantID
                    {city_filter_subquery}
                    ORDER BY
                        CASE WHEN LOWER(TRIM(l2.status)) = 'active' THEN 0 ELSE 1 END,
                        DATE(COALESCE(l2.end_date, '9999-12-31')) DESC,
                        l2.leaseID DESC
                    LIMIT 1
                )
            LEFT JOIN apartments a ON l.apartmentID = a.apartmentID
            LEFT JOIN locations loc ON a.location_id = loc.location_id
            {city_filter_main}
            ORDER BY t.tenantID DESC
        """

        params = []
        city_filter_subquery = ""
        city_filter_main = ""

        if city:
            city_filter_subquery = "AND loc2.city = ?"
            city_filter_main = """
            WHERE EXISTS (
                SELECT 1
                FROM leases l3
                JOIN apartments a3 ON l3.apartmentID = a3.apartmentID
                JOIN locations loc3 ON a3.location_id = loc3.location_id
                WHERE l3.tenantID = t.tenantID
                AND loc3.city = ?
            )
            """
            params = [city, city]

        cursor.execute(
            query.format(
                city_filter_subquery=city_filter_subquery,
                city_filter_main=city_filter_main,
            ),
            tuple(params),
        )

        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def update_tenant(tenant_id, name, NI_number, phone, email):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
        UPDATE tenants
        SET name=?, NI_number=?, phone=?, email=?
        WHERE tenantID=?
        """,
            (name, NI_number, phone, email, tenant_id),
        )

        conn.commit()
        conn.close()

    @staticmethod
    def delete_tenant(tenant_id):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tenants WHERE tenantID=?", (tenant_id,))

        conn.commit()
        conn.close()
