from database.db_manager import DBManager


class LeaseController:

    @staticmethod
    def create_lease(tenant_id, apartment_id, start_date, end_date):

        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO leases (tenant_id, apartment_id, start_date, end_date) VALUES (?, ?, ?, ?)",
            (tenant_id, apartment_id, start_date, end_date)
        )

        conn.commit()
        conn.close()

    @staticmethod
    def get_leases():

        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT leases.id, tenants.name, apartments.city, leases.start_date, leases.end_date
        FROM leases
        JOIN tenants ON leases.tenant_id = tenants.id
        JOIN apartments ON leases.apartment_id = apartments.id
        """)

        data = cursor.fetchall()
        conn.close()

        return data