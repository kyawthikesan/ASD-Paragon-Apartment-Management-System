from datetime import datetime
from database.db_manager import DBManager
from models.payment import Payment
from dao.invoice_dao import InvoiceDAO


class PaymentDAO:
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

    # =========================
    # GET ALL PAYMENTS
    # =========================
    @staticmethod
    def get_all_payments():
        """
        Return all payments with joined invoice, tenant, apartment, and city info.
        Useful for finance dashboards and payment history screens.
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
        ORDER BY p.paymentID DESC
        """)

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