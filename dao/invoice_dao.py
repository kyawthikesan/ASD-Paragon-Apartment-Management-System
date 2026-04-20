from datetime import date
from database.db_manager import DBManager
from models.invoice import Invoice


class InvoiceDAO:
    # =========================
    # CREATE INVOICE
    # =========================
    @staticmethod
    def create_invoice(
        leaseID,
        billing_period_start,
        billing_period_end,
        due_date,
        amount_due,
        status="UNPAID"
    ):
        """
        Insert a new invoice record and return the new invoice ID.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO invoices (
            leaseID,
            billing_period_start,
            billing_period_end,
            due_date,
            amount_due,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            leaseID,
            billing_period_start,
            billing_period_end,
            due_date,
            amount_due,
            status
        ))

        conn.commit()
        invoice_id = cursor.lastrowid
        conn.close()

        return invoice_id

    # =========================
    # CHECK IF INVOICE EXISTS
    # =========================
    @staticmethod
    def invoice_exists_for_period(leaseID, billing_period_start, billing_period_end):
        """
        Prevent duplicate invoices for the same lease and billing period.
        Returns True if an invoice already exists, otherwise False.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT 1
        FROM invoices
        WHERE leaseID = ?
          AND billing_period_start = ?
          AND billing_period_end = ?
        LIMIT 1
        """, (leaseID, billing_period_start, billing_period_end))

        result = cursor.fetchone()
        conn.close()

        return result is not None

    # =========================
    # GET ALL INVOICES
    # =========================
    @staticmethod
    def get_all_invoices():
        """
        Return all invoices with joined tenant, apartment, and city info.
        Good for invoice lists and admin/finance screens.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            i.invoiceID,
            i.leaseID,
            t.name AS tenant_name,
            a.type AS apartment_type,
            loc.city,
            i.billing_period_start,
            i.billing_period_end,
            i.due_date,
            i.amount_due,
            i.status,
            i.created_at
        FROM invoices i
        JOIN leases l ON i.leaseID = l.leaseID
        JOIN tenants t ON l.tenantID = t.tenantID
        JOIN apartments a ON l.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        ORDER BY i.invoiceID DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # =========================
    # GET INVOICE BY ID
    # =========================
    @staticmethod
    def get_invoice_by_id(invoiceID):
        """
        Return one invoice with richer joined details.
        Used when viewing an invoice or building receipt/report info.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            i.invoiceID,
            i.leaseID,
            t.name AS tenant_name,
            a.type AS apartment_type,
            a.rent,
            loc.city,
            i.billing_period_start,
            i.billing_period_end,
            i.due_date,
            i.amount_due,
            i.status,
            i.created_at
        FROM invoices i
        JOIN leases l ON i.leaseID = l.leaseID
        JOIN tenants t ON l.tenantID = t.tenantID
        JOIN apartments a ON l.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        WHERE i.invoiceID = ?
        """, (invoiceID,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    # =========================
    # GET INVOICES BY LEASE
    # =========================
    @staticmethod
    def get_invoices_by_lease(leaseID):
        """
        Return all invoices for a single lease.
        Useful for lease payment history and finance screens.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            invoiceID,
            leaseID,
            billing_period_start,
            billing_period_end,
            due_date,
            amount_due,
            status,
            created_at
        FROM invoices
        WHERE leaseID = ?
        ORDER BY billing_period_start DESC, invoiceID DESC
        """, (leaseID,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # =========================
    # GET OPEN INVOICES
    # =========================
    @staticmethod
    def get_open_invoices():
        """
        Return invoices that still need attention:
        UNPAID, PARTIAL, or LATE.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            i.invoiceID,
            i.leaseID,
            t.name AS tenant_name,
            a.type AS apartment_type,
            loc.city,
            i.billing_period_start,
            i.billing_period_end,
            i.due_date,
            i.amount_due,
            i.status,
            i.created_at
        FROM invoices i
        JOIN leases l ON i.leaseID = l.leaseID
        JOIN tenants t ON l.tenantID = t.tenantID
        JOIN apartments a ON l.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        WHERE i.status IN ('UNPAID', 'PARTIAL', 'LATE')
        ORDER BY i.due_date ASC, i.invoiceID DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # =========================
    # UPDATE INVOICE STATUS
    # =========================
    @staticmethod
    def update_invoice_status(invoiceID, status):
        """
        Update the status of one invoice.
        Expected statuses: UNPAID, PARTIAL, PAID, LATE
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE invoices
        SET status = ?
        WHERE invoiceID = ?
        """, (status, invoiceID))

        conn.commit()
        conn.close()

    # =========================
    # MARK OVERDUE INVOICES
    # =========================
    @staticmethod
    def mark_overdue_invoices():
        """
        Mark invoices as LATE when the due date has passed
        and they are still unpaid or partially paid.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE invoices
        SET status = 'LATE'
        WHERE DATE(due_date) < DATE('now')
          AND status IN ('UNPAID', 'PARTIAL')
        """)

        conn.commit()
        conn.close()

    # =========================
    # DELETE INVOICE
    # =========================
    @staticmethod
    def delete_invoice(invoiceID):
        """
        Delete one invoice by ID.
        Be careful if payments already reference it.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        DELETE FROM invoices
        WHERE invoiceID = ?
        """, (invoiceID,))

        conn.commit()
        conn.close()

    # =========================
    # GET TOTAL PAID
    # =========================
    @staticmethod
    def get_total_paid_for_invoice(invoiceID):
        """
        Sum all payments made against one invoice.
        Returns 0 if no payments exist yet.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM payments
        WHERE invoiceID = ?
        """, (invoiceID,))

        total = cursor.fetchone()[0]
        conn.close()

        return float(total or 0)

    # =========================
    # GET OUTSTANDING BALANCE
    # =========================
    @staticmethod
    def get_outstanding_balance(invoiceID):
        """
        Remaining amount still to be paid for an invoice.
        Never returns a negative value.
        """
        invoice = InvoiceDAO.get_invoice_by_id(invoiceID)
        if not invoice:
            return 0.0

        total_paid = InvoiceDAO.get_total_paid_for_invoice(invoiceID)
        outstanding = float(invoice["amount_due"]) - total_paid

        return max(0.0, outstanding)

    # =========================
    # REFRESH INVOICE STATUS
    # =========================
    @staticmethod
    def refresh_invoice_status(invoiceID):
        """
        Recalculate invoice status based on:
        - amount due
        - total paid
        - due date

        Rules:
        - 0 paid and overdue -> LATE
        - 0 paid and not overdue -> UNPAID
        - partly paid and overdue -> LATE
        - partly paid and not overdue -> PARTIAL
        - fully paid or overpaid -> PAID
        """
        invoice = InvoiceDAO.get_invoice_by_id(invoiceID)
        if not invoice:
            return

        amount_due = float(invoice["amount_due"])
        total_paid = InvoiceDAO.get_total_paid_for_invoice(invoiceID)
        today = date.today().isoformat()

        if total_paid <= 0:
            if invoice["due_date"] < today:
                new_status = "LATE"
            else:
                new_status = "UNPAID"
        elif total_paid < amount_due:
            if invoice["due_date"] < today:
                new_status = "LATE"
            else:
                new_status = "PARTIAL"
        else:
            new_status = "PAID"

        InvoiceDAO.update_invoice_status(invoiceID, new_status)

    # =========================
    # CONVERT TO MODEL OBJECT
    # =========================
    @staticmethod
    def to_model(data):
        """
        Convert a dict-style DB result into an Invoice model object.
        """
        if not data:
            return None

        return Invoice(
            invoiceID=data.get("invoiceID"),
            leaseID=data.get("leaseID"),
            billing_period_start=data.get("billing_period_start"),
            billing_period_end=data.get("billing_period_end"),
            due_date=data.get("due_date"),
            amount_due=data.get("amount_due"),
            status=data.get("status", "UNPAID"),
            created_at=data.get("created_at")
        )