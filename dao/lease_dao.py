from database.db_manager import DBManager
from datetime import date


class LeaseDAO:

    # =========================
    # CREATE LEASE
    # =========================
    @staticmethod
    def create_lease(tenantID, apartmentID, start_date, end_date):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO leases (tenantID, apartmentID, start_date, end_date, status)
        VALUES (?, ?, ?, ?, 'Active')
        """, (tenantID, apartmentID, start_date, end_date))

        conn.commit()
        conn.close()


    # =========================
    # GET ALL LEASES (UI LIST)
    # =========================
    @staticmethod
    def get_all_leases():
        conn = DBManager.get_connection()
        conn.row_factory = lambda cursor, row: {
            "leaseID": row[0],
            "tenant": row[1],
            "apartment": row[2],
            "start_date": row[3],
            "end_date": row[4],
            "status": row[5]
        }
        cursor = conn.cursor()

        cursor.execute("""
        SELECT l.leaseID, t.name, a.type, l.start_date, l.end_date, l.status
        FROM leases l
        JOIN tenants t ON l.tenantID = t.tenantID
        JOIN apartments a ON l.apartmentID = a.apartmentID
        ORDER BY l.leaseID DESC
        """)

        rows = cursor.fetchall()
        conn.close()
        return rows


    # =========================
    # CHECK ACTIVE LEASE (FIXED - DATE BASED)
    # =========================
    @staticmethod
    def has_active_lease(tenantID):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM leases
        WHERE tenantID = ?
        AND DATE(end_date) >= DATE('now')
        """, (tenantID,))

        result = cursor.fetchone()
        conn.close()
        return result is not None


    # =========================
    # CHECK APARTMENT AVAILABILITY
    # =========================
    @staticmethod
    def is_apartment_available(apartmentID):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT status
        FROM apartments
        WHERE apartmentID = ?
        """, (apartmentID,))

        result = cursor.fetchone()
        conn.close()

        return result and result["status"] == "Available"


    # =========================
    # MARK APARTMENT OCCUPIED
    # =========================
    @staticmethod
    def mark_apartment_occupied(apartmentID):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE apartments
        SET status = 'Occupied'
        WHERE apartmentID = ?
        """, (apartmentID,))

        conn.commit()
        conn.close()


    # =========================
    # AUTO EXPIRE OLD LEASES (IMPORTANT FIX)
    # =========================
    @staticmethod
    def expire_leases():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        #expire lease
        cursor.execute("""
        UPDATE leases
        SET status = 'Ended'
        WHERE DATE(end_date) < DATE('now')
        AND status = 'Active'
        """)

        #free apartments
        cursor.execute("""
        UPDATE apartments
        SET status = 'Available'
        WHERE apartmentID IN (
            SELECT apartmentID FROM leases
            WHERE DATE(end_date) < DATE('now')
        )
        """)

        conn.commit()
        conn.close()