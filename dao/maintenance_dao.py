from datetime import datetime
from database.db_manager import DBManager


class MaintenanceDAO:
    @staticmethod
    def add_request(apartmentID, tenantID, title, description, priority="Medium", status="Open"):
        now = datetime.now().isoformat(timespec="seconds")
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_requests (
                apartmentID, tenantID, title, description, priority, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (apartmentID, tenantID, title, description, priority, status, now, now),
        )
        conn.commit()
        request_id = cursor.lastrowid
        conn.close()
        return request_id

    @staticmethod
    def get_all_requests(city=None):
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        query = """
            SELECT
                m.requestID,
                m.apartmentID,
                a.type AS apartment_type,
                loc.city,
                m.tenantID,
                t.name AS tenant_name,
                m.title,
                m.description,
                m.priority,
                m.status,
                m.created_at,
                m.updated_at
            FROM maintenance_requests m
            LEFT JOIN apartments a ON m.apartmentID = a.apartmentID
            LEFT JOIN locations loc ON a.location_id = loc.location_id
            LEFT JOIN tenants t ON m.tenantID = t.tenantID
            """
        params = []
        if city:
            query += " WHERE loc.city = ?"
            params.append(city)
        query += " ORDER BY m.requestID DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def update_request_status(request_id, status):
        now = datetime.now().isoformat(timespec="seconds")
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE maintenance_requests
            SET status = ?, updated_at = ?
            WHERE requestID = ?
            """,
            (status, now, request_id),
        )
        conn.commit()
        conn.close()
