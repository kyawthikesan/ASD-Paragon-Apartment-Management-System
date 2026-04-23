# Student Name: Kyaw Thike (oliver) San
# Student ID: 25014001
# Module: UFCF8S-30-2 Advanced Software Development
from datetime import datetime
from database.db_manager import DBManager
from models.payment import Payment
from dao.invoice_dao import InvoiceDAO


class PaymentDAO:
    @staticmethod
    def _table_columns(cursor, table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row["name"] for row in cursor.fetchall()}

    # =========================
    # GENERATE RECEIPT NUMBER
    # =========================
    @staticmethod
    def generate_receipt_number():
        """
        Create a simple unique receipt number using current timestamp.
        Example: RCT-20260420194530
        """
        return "RCT-" + datetime.now().strftime("%Y%m%d%H%M%S")

    # =========================
    # RECORD PAYMENT
    # =========================
    @staticmethod
    def create_payment(invoiceID, payment_date, amount_paid, payment_method="MANUAL", receipt_number=None):
        """
        Insert a payment record for an invoice.
        After saving, refresh the invoice status automatically.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        if receipt_number is None:
            receipt_number = PaymentDAO.generate_receipt_number()

        cursor.execute("""
        INSERT INTO payments (
            invoiceID,
            payment_date,
            amount_paid,
            payment_method,
            receipt_number
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            invoiceID,
            payment_date,
            amount_paid,
            payment_method,
            receipt_number
        ))

        conn.commit()
        payment_id = cursor.lastrowid
        conn.close()

        # Recalculate invoice status after payment is recorded
        InvoiceDAO.refresh_invoice_status(invoiceID)

        return payment_id

    @staticmethod
    def add_payment(tenantID, apartmentID, amount, payment_date, method="MANUAL", status="Pending", note=None):
        """
        Insert a payment using the active DB schema.
        Supports both:
        - modern schema (tenantID/apartmentID/amount/method/status/note)
        - legacy invoice schema (requires invoice flow; not used by current controller tests)
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        payment_columns = PaymentDAO._table_columns(cursor, "payments")

        if {"tenantID", "apartmentID"}.issubset(payment_columns):
            columns = ["tenantID", "apartmentID", "payment_date"]
            values = [tenantID, apartmentID, payment_date]

            if "amount" in payment_columns:
                columns.append("amount")
            else:
                columns.append("amount_paid")
            values.append(amount)

            if "method" in payment_columns:
                columns.append("method")
            else:
                columns.append("payment_method")
            values.append(method)

            if "status" in payment_columns:
                columns.append("status")
                values.append(status)

            if "note" in payment_columns:
                columns.append("note")
                values.append(note)

            placeholders = ", ".join(["?"] * len(values))
            column_sql = ", ".join(columns)

            cursor.execute(
                f"INSERT INTO payments ({column_sql}) VALUES ({placeholders})",
                tuple(values),
            )
            conn.commit()
            payment_id = cursor.lastrowid
            conn.close()
            return payment_id

        conn.close()
        raise ValueError("payments table does not support tenant/apartment payment inserts")

    @staticmethod
    def update_payment_status(payment_id, status):
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        payment_columns = PaymentDAO._table_columns(cursor, "payments")

        if "status" not in payment_columns:
            conn.close()
            return False

        cursor.execute(
            """
            UPDATE payments
            SET status = ?
            WHERE paymentID = ?
            """,
            (status, payment_id),
        )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    # =========================
    # GET ALL PAYMENTS
    # =========================
    @staticmethod
    def get_all_payments(city=None):
        """
        Return all payments with joined invoice, tenant, apartment, and city info.
        Useful for finance dashboards and payment history screens.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        payment_columns = PaymentDAO._table_columns(cursor, "payments")

        # Legacy schema: payments are linked through invoices.
        if "invoiceID" in payment_columns:
            query = """
            SELECT
                p.paymentID,
                p.invoiceID,
                i.leaseID,
                t.name AS tenant_name,
                a.type AS apartment_type,
                loc.city,
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
            """
            params = []
            if city:
                query += " WHERE loc.city = ?"
                params.append(city)
            query += " ORDER BY p.paymentID DESC"
            cursor.execute(query, tuple(params))
        else:
            amount_col = "amount" if "amount" in payment_columns else "amount_paid"
            method_col = "method" if "method" in payment_columns else "payment_method"
            status_expr = "p.status" if "status" in payment_columns else "NULL"
            note_expr = "p.note" if "note" in payment_columns else "NULL"

            query = f"""
            SELECT
                p.paymentID,
                NULL AS invoiceID,
                NULL AS leaseID,
                p.tenantID,
                p.apartmentID,
                t.name AS tenant_name,
                a.type AS apartment_type,
                loc.city,
                p.payment_date,
                p.{amount_col} AS amount_paid,
                p.{method_col} AS payment_method,
                {status_expr} AS status,
                {note_expr} AS note,
                NULL AS receipt_number,
                NULL AS created_at
            FROM payments p
            LEFT JOIN tenants t ON p.tenantID = t.tenantID
            LEFT JOIN apartments a ON p.apartmentID = a.apartmentID
            LEFT JOIN locations loc ON a.location_id = loc.location_id
            """
            params = []
            if city:
                query += " WHERE loc.city = ?"
                params.append(city)
            query += " ORDER BY p.paymentID DESC"
            cursor.execute(query, tuple(params))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # =========================
    # GET PAYMENT BY ID
    # =========================
    @staticmethod
    def get_payment_by_id(paymentID):
        """
        Return one payment by its ID with joined context data.
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
            loc.city,
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
        WHERE p.paymentID = ?
        """, (paymentID,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    # =========================
    # GET PAYMENTS BY INVOICE
    # =========================
    @staticmethod
    def get_payments_by_invoice(invoiceID):
        """
        Return all payments linked to one invoice.
        Useful when viewing invoice settlement history.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            paymentID,
            invoiceID,
            payment_date,
            amount_paid,
            payment_method,
            receipt_number,
            created_at
        FROM payments
        WHERE invoiceID = ?
        ORDER BY payment_date DESC, paymentID DESC
        """, (invoiceID,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # =========================
    # GET PAYMENTS BY LEASE
    # =========================
    @staticmethod
    def get_payments_by_lease(leaseID):
        """
        Return all payments for a specific lease.
        This helps build lease payment history views.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            p.paymentID,
            p.invoiceID,
            i.leaseID,
            p.payment_date,
            p.amount_paid,
            p.payment_method,
            p.receipt_number,
            p.created_at
        FROM payments p
        JOIN invoices i ON p.invoiceID = i.invoiceID
        WHERE i.leaseID = ?
        ORDER BY p.payment_date DESC, p.paymentID DESC
        """, (leaseID,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # =========================
    # GET TOTAL PAID BY LEASE
    # =========================
    @staticmethod
    def get_total_paid_by_lease(leaseID):
        """
        Return the total amount paid across all invoices for one lease.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT COALESCE(SUM(p.amount_paid), 0)
        FROM payments p
        JOIN invoices i ON p.invoiceID = i.invoiceID
        WHERE i.leaseID = ?
        """, (leaseID,))

        total = cursor.fetchone()[0]
        conn.close()

        return float(total or 0)

    # =========================
    # GET RECEIPT DATA
    # =========================
    @staticmethod
    def get_receipt_data(paymentID):
        """
        Return everything needed to display or print a receipt.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            p.paymentID,
            p.receipt_number,
            p.payment_date,
            p.amount_paid,
            p.payment_method,
            i.invoiceID,
            i.billing_period_start,
            i.billing_period_end,
            i.amount_due,
            i.due_date,
            i.status AS invoice_status,
            l.leaseID,
            t.name AS tenant_name,
            a.type AS apartment_type,
            a.rent,
            loc.city
        FROM payments p
        JOIN invoices i ON p.invoiceID = i.invoiceID
        JOIN leases l ON i.leaseID = l.leaseID
        JOIN tenants t ON l.tenantID = t.tenantID
        JOIN apartments a ON l.apartmentID = a.apartmentID
        LEFT JOIN locations loc ON a.location_id = loc.location_id
        WHERE p.paymentID = ?
        """, (paymentID,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    # =========================
    # DELETE PAYMENT
    # =========================
    @staticmethod
    def delete_payment(paymentID):
        """
        Delete a payment and refresh the related invoice status.
        """
        conn = DBManager.get_connection()
        cursor = conn.cursor()

        # Find related invoice before deleting
        cursor.execute("""
        SELECT invoiceID
        FROM payments
        WHERE paymentID = ?
        """, (paymentID,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        invoiceID = row["invoiceID"]

        cursor.execute("""
        DELETE FROM payments
        WHERE paymentID = ?
        """, (paymentID,))

        conn.commit()
        conn.close()

        # Refresh invoice after deletion
        InvoiceDAO.refresh_invoice_status(invoiceID)

        return True

    # =========================
    # CONVERT TO MODEL OBJECT
    # =========================
    @staticmethod
    def to_model(data):
        """
        Convert a dict-style DB result into a Payment model object.
        """
        if not data:
            return None

        return Payment(
            paymentID=data.get("paymentID"),
            invoiceID=data.get("invoiceID"),
            payment_date=data.get("payment_date"),
            amount_paid=data.get("amount_paid"),
            payment_method=data.get("payment_method", "MANUAL"),
            receipt_number=data.get("receipt_number"),
            created_at=data.get("created_at")
        )
