from database.db_manager import DBManager


class MaintenanceDAO:
    """
    DAO for maintenance requests.

    The app now stores maintenance data in `maintenance_requests` inside `pams.db`.
    This class keeps both the modern static API used by controllers and a small
    compatibility layer used by the legacy maintenance view/tests.
    """

    def __init__(self, _db_path=None):
        # `_db_path` kept only for backward compatibility with older tests.
        pass

    @staticmethod
    def add_request(apartmentID, tenantID, title, description, priority="Medium", status="Open"):
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_requests (
                apartmentID,
                tenantID,
                title,
                description,
                priority,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (apartmentID, tenantID, title, description, priority, status),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_requests(city=None):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            mr.requestID,
            mr.apartmentID,
            mr.tenantID,
            mr.title,
            mr.description,
            mr.priority,
            mr.status,
            mr.created_at,
            mr.updated_at,
            t.name AS tenant_name,
            a.type AS apartment_type,
            loc.city
        FROM maintenance_requests mr
        LEFT JOIN tenants t ON mr.tenantID = t.tenantID
        LEFT JOIN apartments a ON mr.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        """
        params = []
        if city:
            query += " WHERE loc.city = ?"
            params.append(city)
        query += " ORDER BY mr.requestID DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    @staticmethod
    def update_request_status(request_id, status):
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE maintenance_requests
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE requestID = ?
            """,
            (status, request_id),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_cost_report_data(city=None):
        """
        Compatibility helper for the legacy maintenance view.
        Current schema does not store cost/hours, so those totals are zero.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        query = """
        SELECT COUNT(*) AS resolved_count
        FROM maintenance_requests mr
        LEFT JOIN apartments a ON mr.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        WHERE LOWER(TRIM(mr.status)) = 'resolved'
        """
        params = []
        if city:
            query += " AND loc.city = ?"
            params.append(city)

        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
        conn.close()

        resolved_count = int(row["resolved_count"] or 0)
        return 0.0, 0, resolved_count

    # -------------------------
    # Legacy compatibility API
    # -------------------------
    def log_request(self, complaint_id):
        # Preserve legacy call shape by creating a generic request.
        self.add_request(
            apartmentID=None,
            tenantID=None,
            title=f"Legacy complaint #{complaint_id}",
            description="Migrated from legacy maintenance view flow.",
            priority="Medium",
            status="Open",
        )

    def update_maintenance(self, req_id, staff, date, status, cost, hours):
        # Legacy scheduler updates only map cleanly to status in new schema.
        self.update_request_status(req_id, status)
