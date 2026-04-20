from database.db_manager import DBManager
from dao.invoice_dao import InvoiceDAO


class ReportDAO:
    # =========================
    # OVERALL FINANCIAL SUMMARY
    # =========================
    @staticmethod
    def get_overall_financial_summary():
        """
        Return overall finance totals across the whole system:
        - total invoiced
        - total collected
        - total pending
        - invoice counts
        """
        # Make sure overdue invoices are updated before reporting
        InvoiceDAO.mark_overdue_invoices()

        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            COALESCE(SUM(amount_due), 0) AS total_invoiced,
            COUNT(*) AS invoice_count,
            SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END) AS paid_invoice_count,
            SUM(CASE WHEN status = 'LATE' THEN 1 ELSE 0 END) AS late_invoice_count
        FROM invoices
        """)
        invoice_row = cursor.fetchone()

        cursor.execute("""
        SELECT COALESCE(SUM(amount_paid), 0) AS total_collected
        FROM payments
        """)
        payment_row = cursor.fetchone()

        conn.close()

        total_invoiced = float(invoice_row["total_invoiced"] or 0)
        total_collected = float(payment_row["total_collected"] or 0)
        total_pending = max(0.0, total_invoiced - total_collected)

        return {
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "total_pending": total_pending,
            "invoice_count": invoice_row["invoice_count"] or 0,
            "paid_invoice_count": invoice_row["paid_invoice_count"] or 0,
            "late_invoice_count": invoice_row["late_invoice_count"] or 0
        }

    # =========================
    # FINANCIAL SUMMARY BY CITY
    # =========================
    @staticmethod
    def get_financial_summary_by_city():
        """
        Return collected vs pending rent grouped by city.
        This is one of your key deliverables.
        """
        InvoiceDAO.mark_overdue_invoices()

        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            COALESCE(loc.city, 'Unknown') AS city,
            COALESCE(SUM(i.amount_due), 0) AS total_invoiced,
            COALESCE((
                SELECT SUM(p.amount_paid)
                FROM payments p
                JOIN invoices i2 ON p.invoiceID = i2.invoiceID
                JOIN leases l2 ON i2.leaseID = l2.leaseID
                JOIN apartments a2 ON l2.apartmentID = a2.apartmentID
                LEFT JOIN locations loc2 ON a2.location_id = loc2.location_id
                WHERE COALESCE(loc2.city, 'Unknown') = COALESCE(loc.city, 'Unknown')
            ), 0) AS total_collected,
            COUNT(i.invoiceID) AS invoice_count,
            SUM(CASE WHEN i.status = 'LATE' THEN 1 ELSE 0 END) AS late_invoice_count
        FROM invoices i
        JOIN leases l ON i.leaseID = l.leaseID
        JOIN apartments a ON l.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        GROUP BY COALESCE(loc.city, 'Unknown')
        ORDER BY city
        """)

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            total_invoiced = float(row["total_invoiced"] or 0)
            total_collected = float(row["total_collected"] or 0)
            total_pending = max(0.0, total_invoiced - total_collected)

            results.append({
                "city": row["city"],
                "total_invoiced": total_invoiced,
                "total_collected": total_collected,
                "total_pending": total_pending,
                "invoice_count": row["invoice_count"] or 0,
                "late_invoice_count": row["late_invoice_count"] or 0
            })

        return results

    # =========================
    # OCCUPANCY REPORT BY CITY
    # =========================
    @staticmethod
    def get_occupancy_report_by_city():
        """
        Return apartment occupancy grouped by city:
        - total apartments
        - occupied apartments
        - available apartments
        - occupancy rate
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            COALESCE(loc.city, 'Unknown') AS city,
            COUNT(a.apartmentID) AS total_apartments,
            SUM(CASE WHEN a.status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied_apartments,
            SUM(CASE WHEN a.status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_apartments
        FROM apartments a
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        GROUP BY COALESCE(loc.city, 'Unknown')
        ORDER BY city
        """)

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            total_apartments = int(row["total_apartments"] or 0)
            occupied_apartments = int(row["occupied_apartments"] or 0)
            available_apartments = int(row["available_apartments"] or 0)

            if total_apartments > 0:
                occupancy_rate = round((occupied_apartments / total_apartments) * 100, 2)
            else:
                occupancy_rate = 0.0

            results.append({
                "city": row["city"],
                "total_apartments": total_apartments,
                "occupied_apartments": occupied_apartments,
                "available_apartments": available_apartments,
                "occupancy_rate": occupancy_rate
            })

        return results

    # =========================
    # OVERALL OCCUPANCY SUMMARY
    # =========================
    @staticmethod
    def get_overall_occupancy_summary():
        """
        Return one overall occupancy summary for the whole system.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            COUNT(apartmentID) AS total_apartments,
            SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied_apartments,
            SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_apartments
        FROM apartments
        """)

        row = cursor.fetchone()
        conn.close()

        total_apartments = int(row["total_apartments"] or 0)
        occupied_apartments = int(row["occupied_apartments"] or 0)
        available_apartments = int(row["available_apartments"] or 0)

        if total_apartments > 0:
            occupancy_rate = round((occupied_apartments / total_apartments) * 100, 2)
        else:
            occupancy_rate = 0.0

        return {
            "total_apartments": total_apartments,
            "occupied_apartments": occupied_apartments,
            "available_apartments": available_apartments,
            "occupancy_rate": occupancy_rate
        }

    # =========================
    # LATE PAYMENT ALERTS
    # =========================
    @staticmethod
    def get_late_invoices():
        """
        Return invoices currently marked as LATE with tenant and city info.
        Useful for alert examples and dashboard warnings.
        """
        InvoiceDAO.mark_overdue_invoices()

        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            i.invoiceID,
            i.leaseID,
            t.name AS tenant_name,
            a.type AS apartment_type,
            COALESCE(loc.city, 'Unknown') AS city,
            i.billing_period_start,
            i.billing_period_end,
            i.due_date,
            i.amount_due,
            i.status,
            COALESCE((
                SELECT SUM(p.amount_paid)
                FROM payments p
                WHERE p.invoiceID = i.invoiceID
            ), 0) AS total_paid
        FROM invoices i
        JOIN leases l ON i.leaseID = l.leaseID
        JOIN tenants t ON l.tenantID = t.tenantID
        JOIN apartments a ON l.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        WHERE i.status = 'LATE'
        ORDER BY i.due_date ASC, i.invoiceID DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            amount_due = float(row["amount_due"] or 0)
            total_paid = float(row["total_paid"] or 0)
            outstanding_balance = max(0.0, amount_due - total_paid)

            results.append({
                "invoiceID": row["invoiceID"],
                "leaseID": row["leaseID"],
                "tenant_name": row["tenant_name"],
                "apartment_type": row["apartment_type"],
                "city": row["city"],
                "billing_period_start": row["billing_period_start"],
                "billing_period_end": row["billing_period_end"],
                "due_date": row["due_date"],
                "amount_due": amount_due,
                "total_paid": total_paid,
                "outstanding_balance": outstanding_balance,
                "status": row["status"]
            })

        return results

    # =========================
    # LEASE PAYMENT HISTORY
    # =========================
    @staticmethod
    def get_lease_payment_history(leaseID):
        """
        Return invoice-by-invoice payment history for a lease.
        Includes:
        - invoice amount
        - total paid
        - outstanding balance
        - status
        """
        InvoiceDAO.mark_overdue_invoices()

        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            i.invoiceID,
            i.leaseID,
            i.billing_period_start,
            i.billing_period_end,
            i.due_date,
            i.amount_due,
            i.status,
            i.created_at,
            COALESCE(SUM(p.amount_paid), 0) AS total_paid
        FROM invoices i
        LEFT JOIN payments p ON i.invoiceID = p.invoiceID
        WHERE i.leaseID = ?
        GROUP BY
            i.invoiceID,
            i.leaseID,
            i.billing_period_start,
            i.billing_period_end,
            i.due_date,
            i.amount_due,
            i.status,
            i.created_at
        ORDER BY i.billing_period_start DESC, i.invoiceID DESC
        """, (leaseID,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            amount_due = float(row["amount_due"] or 0)
            total_paid = float(row["total_paid"] or 0)
            outstanding_balance = max(0.0, amount_due - total_paid)

            results.append({
                "invoiceID": row["invoiceID"],
                "leaseID": row["leaseID"],
                "billing_period_start": row["billing_period_start"],
                "billing_period_end": row["billing_period_end"],
                "due_date": row["due_date"],
                "amount_due": amount_due,
                "total_paid": total_paid,
                "outstanding_balance": outstanding_balance,
                "status": row["status"],
                "created_at": row["created_at"]
            })

        return results

    # =========================
    # CITY PAYMENT HISTORY
    # =========================
    @staticmethod
    def get_payment_history_by_city(city):
        """
        Return payment records filtered by city.
        Useful for finance reports and review screens.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            p.paymentID,
            p.invoiceID,
            i.leaseID,
            t.name AS tenant_name,
            a.type AS apartment_type,
            COALESCE(loc.city, 'Unknown') AS city,
            p.payment_date,
            p.amount_paid,
            p.payment_method,
            p.receipt_number,
            p.created_at
        FROM payments p
        JOIN invoices i ON p.invoiceID = i.invoiceID
        JOIN leases l ON i.leaseID = l.leaseID
        JOIN tenants t ON l.tenantID = t.tenantID
        JOIN apartments a ON l.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        WHERE COALESCE(loc.city, 'Unknown') = ?
        ORDER BY p.payment_date DESC, p.paymentID DESC
        """, (city,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]