# Student Name: Kyaw Thike (oliver) San
# Student ID: 25014001
# Module: UFCF8S-30-2 Advanced Software Development
from database.db_manager import DBManager


class MaintenanceDAO:
    """
    DAO for maintenance requests in pams.db.
    """

    def __init__(self, _db_path=None):
        # Kept only for backward compatibility with older code/tests.
        pass

    @staticmethod
    def add_request(
        apartmentID,
        tenantID,
        title,
        description,
        priority="Medium",
        status="Open",
    ):
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
            mr.scheduled_date,
            mr.scheduled_time,
            mr.assigned_staff,
            mr.resolution_note,
            mr.hours_spent,
            mr.cost,
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
    def get_request_by_id(request_id):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM maintenance_requests
            WHERE requestID = ?
            """,
            (request_id,),
        )

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

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
    def schedule_request(request_id, assigned_staff, scheduled_date, scheduled_time, priority=None):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        if priority is not None:
            cursor.execute(
                """
                UPDATE maintenance_requests
                SET
                    assigned_staff = ?,
                    scheduled_date = ?,
                    scheduled_time = ?,
                    priority = ?,
                    status = 'Scheduled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE requestID = ?
                """,
                (assigned_staff, scheduled_date, scheduled_time, priority, request_id),
            )
        else:
            cursor.execute(
                """
                UPDATE maintenance_requests
                SET
                    assigned_staff = ?,
                    scheduled_date = ?,
                    scheduled_time = ?,
                    status = 'Scheduled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE requestID = ?
                """,
                (assigned_staff, scheduled_date, scheduled_time, request_id),
            )

        conn.commit()
        conn.close()

    @staticmethod
    def resolve_request(request_id, resolution_note, hours_spent, cost):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE maintenance_requests
            SET
                resolution_note = ?,
                hours_spent = ?,
                cost = ?,
                status = 'Resolved',
                updated_at = CURRENT_TIMESTAMP
            WHERE requestID = ?
            """,
            (resolution_note, hours_spent, cost, request_id),
        )

        conn.commit()
        conn.close()

    @staticmethod
    def get_cost_report_data(city=None):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            COALESCE(SUM(mr.cost), 0) AS total_cost,
            COALESCE(SUM(mr.hours_spent), 0) AS total_hours,
            COUNT(*) AS resolved_count
        FROM maintenance_requests mr
        LEFT JOIN apartments a
            ON mr.apartmentID = a.apartmentID
        LEFT JOIN locations loc
            ON a.location_id = loc.location_id
        WHERE LOWER(TRIM(mr.status)) = 'resolved'
        """
        params = []

        if city:
            query += " AND loc.city = ?"
            params.append(city)

        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
        conn.close()

        return (
            float(row["total_cost"] or 0),
            float(row["total_hours"] or 0),
            int(row["resolved_count"] or 0),
        )

    @staticmethod
    def get_all_tenant_ids():
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT tenantID FROM tenants ORDER BY tenantID")
        rows = cursor.fetchall()
        conn.close()
        return [str(row["tenantID"]) for row in rows]

    @staticmethod
    def get_current_apartment_by_tenant(tenant_id):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT apartmentID
            FROM leases
            WHERE tenantID = ?
              AND LOWER(TRIM(status)) = 'active'
            ORDER BY leaseID DESC
            LIMIT 1
            """,
            (tenant_id,)
        )

        row = cursor.fetchone()
        conn.close()

        return row["apartmentID"] if row else None

    # -------------------------
    # Legacy compatibility API
    # -------------------------
    def log_request(self, complaint_id):
        self.add_request(
            apartmentID=None,
            tenantID=None,
            title=f"Legacy complaint #{complaint_id}",
            description="Migrated from legacy maintenance flow.",
            priority="Medium",
            status="Open",
        )

    def update_maintenance(self, req_id, staff, date, status, cost, hours):
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE maintenance_requests
            SET
                assigned_staff = ?,
                scheduled_date = ?,
                status = ?,
                cost = ?,
                hours_spent = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE requestID = ?
            """,
            (staff, date, status, cost, hours, req_id),
        )

        conn.commit()
        conn.close()
    @staticmethod
    def get_tenant_options():
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT tenantID, name, NI_number
            FROM tenants
            ORDER BY name
            """
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "tenantID": row["tenantID"],
                "label": f'{row["name"]} - {row["NI_number"]}'
            }
            for row in rows
        ]
        
