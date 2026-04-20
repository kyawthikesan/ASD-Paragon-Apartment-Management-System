import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import date, datetime, timedelta

from dao.lease_dao import LeaseDAO
from dao.invoice_dao import InvoiceDAO
from dao.payment_dao import PaymentDAO
from dao.report_dao import ReportDAO


class FinanceDashboardView(ttk.Frame):
    def __init__(self, parent, logout_callback=None, home_callback=None, initial_tab="Invoices"):
        super().__init__(parent)
        self.parent = parent
        self.logout_callback = logout_callback
        self.home_callback = home_callback
      

        self.pack(fill="both", expand=True)

        self.lease_map = {}
        self.invoice_map = {}

        self._build_layout()
        self.refresh_all()
        self.initial_tab = initial_tab

    # =========================
    # MAIN LAYOUT
    # =========================
    def _build_layout(self):
        top_bar = ttk.Frame(self, padding=12)
        top_bar.pack(fill="x")

        ttk.Label(
            top_bar,
            text="Finance Dashboard",
            font=("Arial", 18, "bold")
        ).pack(side="left")

        if self.home_callback:
            ttk.Button(
                top_bar,
                text="← Home",
                command=self.home_callback
            ).pack(side="right", padx=6)

        ttk.Button(
            top_bar,
            text="Refresh",
            command=self.refresh_all
        ).pack(side="right", padx=6)

        if self.logout_callback:
            ttk.Button(
                top_bar,
                text="Logout",
                command=self.logout_callback
            ).pack(side="right", padx=6)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.invoice_tab = ttk.Frame(self.notebook, padding=12)
        self.payment_tab = ttk.Frame(self.notebook, padding=12)
        self.report_tab = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.invoice_tab, text="Invoices")
        self.notebook.add(self.payment_tab, text="Payments")
        self.notebook.add(self.report_tab, text="Reports")

        self._build_invoice_tab()
        self._build_payment_tab()
        self._build_report_tab()
    def _select_initial_tab(self):
        tab_map = {
            "Invoices": self.invoice_tab,
            "Payments": self.payment_tab,
            "Reports": self.report_tab,
        }
        target = tab_map.get(self.initial_tab, self.invoice_tab)
        self.notebook.select(target)

    # =========================
    # INVOICE TAB
    # =========================
    def _build_invoice_tab(self):
        """
        Build invoice generation form and invoice table.
        """
        form = ttk.LabelFrame(self.invoice_tab, text="Generate Invoice", padding=12)
        form.pack(fill="x", pady=(0, 12))

        ttk.Label(form, text="Lease").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.lease_combo = ttk.Combobox(form, state="readonly", width=60)
        self.lease_combo.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        self.lease_combo.bind("<<ComboboxSelected>>", self._on_lease_selected)

        ttk.Label(form, text="Billing Start (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.billing_start_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.billing_start_var, width=25).grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="Billing End (YYYY-MM-DD)").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.billing_end_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.billing_end_var, width=25).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="Due Date (YYYY-MM-DD)").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        self.invoice_due_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.invoice_due_var, width=25).grid(row=3, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="Amount Due").grid(row=4, column=0, sticky="w", padx=6, pady=6)
        self.amount_due_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.amount_due_var, width=25).grid(row=4, column=1, sticky="w", padx=6, pady=6)

        ttk.Button(
            form,
            text="Generate Invoice",
            command=self.create_invoice
        ).grid(row=5, column=1, sticky="w", padx=6, pady=(10, 0))

        form.columnconfigure(1, weight=1)

        list_frame = ttk.LabelFrame(self.invoice_tab, text="All Invoices", padding=12)
        list_frame.pack(fill="both", expand=True)

        invoice_actions = ttk.Frame(list_frame)
        invoice_actions.pack(fill="x", pady=(0, 8))

        ttk.Button(
            invoice_actions,
            text="Download Selected Invoice PDF",
            command=self.export_selected_invoice_pdf
        ).pack(side="right")

        columns = ("invoiceID", "tenant_name", "city", "period", "due_date", "amount_due", "status")
        self.invoice_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)

        self.invoice_tree.heading("invoiceID", text="Invoice ID")
        self.invoice_tree.heading("tenant_name", text="Tenant")
        self.invoice_tree.heading("city", text="City")
        self.invoice_tree.heading("period", text="Billing Period")
        self.invoice_tree.heading("due_date", text="Due Date")
        self.invoice_tree.heading("amount_due", text="Amount Due")
        self.invoice_tree.heading("status", text="Status")

        self.invoice_tree.column("invoiceID", width=90, anchor="center")
        self.invoice_tree.column("tenant_name", width=160)
        self.invoice_tree.column("city", width=120)
        self.invoice_tree.column("period", width=220)
        self.invoice_tree.column("due_date", width=110, anchor="center")
        self.invoice_tree.column("amount_due", width=110, anchor="e")
        self.invoice_tree.column("status", width=100, anchor="center")

        self.invoice_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.invoice_tree.yview)
        self.invoice_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    # =========================
    # PAYMENT TAB
    # =========================
    def _build_payment_tab(self):
        """
        Build payment entry form and payment history table.
        """
        form = ttk.LabelFrame(self.payment_tab, text="Record Payment", padding=12)
        form.pack(fill="x", pady=(0, 12))

        ttk.Label(form, text="Open Invoice").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.open_invoice_combo = ttk.Combobox(form, state="readonly", width=65)
        self.open_invoice_combo.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        self.open_invoice_combo.bind("<<ComboboxSelected>>", self._on_invoice_selected_for_payment)

        ttk.Label(form, text="Payment Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.payment_date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(form, textvariable=self.payment_date_var, width=25).grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="Amount Paid").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.amount_paid_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.amount_paid_var, width=25).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="Payment Method").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        self.payment_method_combo = ttk.Combobox(
            form,
            state="readonly",
            values=["MANUAL", "CASH", "BANK_TRANSFER", "CARD"],
            width=22
        )
        self.payment_method_combo.grid(row=3, column=1, sticky="w", padx=6, pady=6)
        self.payment_method_combo.set("MANUAL")

        ttk.Button(
            form,
            text="Record Payment",
            command=self.record_payment
        ).grid(row=4, column=1, sticky="w", padx=6, pady=(10, 0))

        form.columnconfigure(1, weight=1)

        list_frame = ttk.LabelFrame(self.payment_tab, text="Payment History", padding=12)
        list_frame.pack(fill="both", expand=True)

        payment_actions = ttk.Frame(list_frame)
        payment_actions.pack(fill="x", pady=(0, 8))

        ttk.Button(
            payment_actions,
            text="Download Selected Receipt PDF",
            command=self.export_selected_payment_pdf
        ).pack(side="right")

        columns = ("paymentID", "tenant_name", "city", "payment_date", "amount_paid", "payment_method", "receipt_number")
        self.payment_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)

        self.payment_tree.heading("paymentID", text="Payment ID")
        self.payment_tree.heading("tenant_name", text="Tenant")
        self.payment_tree.heading("city", text="City")
        self.payment_tree.heading("payment_date", text="Payment Date")
        self.payment_tree.heading("amount_paid", text="Amount Paid")
        self.payment_tree.heading("payment_method", text="Method")
        self.payment_tree.heading("receipt_number", text="Receipt No.")

        self.payment_tree.column("paymentID", width=90, anchor="center")
        self.payment_tree.column("tenant_name", width=160)
        self.payment_tree.column("city", width=120)
        self.payment_tree.column("payment_date", width=120, anchor="center")
        self.payment_tree.column("amount_paid", width=100, anchor="e")
        self.payment_tree.column("payment_method", width=120, anchor="center")
        self.payment_tree.column("receipt_number", width=160, anchor="center")

        self.payment_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.payment_tree.yview)
        self.payment_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    # =========================
    # REPORT TAB
    # =========================
    def _build_report_tab(self):
        """
        Build overall summary, city summary, and late payment alert sections.
        """
        toolbar = ttk.Frame(self.report_tab)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Download CSV",
            command=self.export_reports_csv
        ).pack(side="right", padx=6)

        ttk.Button(
            toolbar,
            text="Download PDF",
            command=self.export_reports_pdf
        ).pack(side="right", padx=6)
        summary_frame = ttk.LabelFrame(self.report_tab, text="Overall Financial Summary", padding=12)
        summary_frame.pack(fill="x", pady=(0, 12))

        self.total_invoiced_var = tk.StringVar(value="0.00")
        self.total_collected_var = tk.StringVar(value="0.00")
        self.total_pending_var = tk.StringVar(value="0.00")
        self.late_invoice_count_var = tk.StringVar(value="0")

        ttk.Label(summary_frame, text="Total Invoiced:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(summary_frame, textvariable=self.total_invoiced_var).grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(summary_frame, text="Total Collected:").grid(row=0, column=2, sticky="w", padx=6, pady=4)
        ttk.Label(summary_frame, textvariable=self.total_collected_var).grid(row=0, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(summary_frame, text="Total Pending:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(summary_frame, textvariable=self.total_pending_var).grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(summary_frame, text="Late Invoices:").grid(row=1, column=2, sticky="w", padx=6, pady=4)
        ttk.Label(summary_frame, textvariable=self.late_invoice_count_var).grid(row=1, column=3, sticky="w", padx=6, pady=4)

        city_frame = ttk.LabelFrame(self.report_tab, text="Financial Summary by City", padding=12)
        city_frame.pack(fill="both", expand=True, pady=(0, 12))

        city_columns = ("city", "total_invoiced", "total_collected", "total_pending", "late_invoice_count")
        self.city_tree = ttk.Treeview(city_frame, columns=city_columns, show="headings", height=8)

        self.city_tree.heading("city", text="City")
        self.city_tree.heading("total_invoiced", text="Total Invoiced")
        self.city_tree.heading("total_collected", text="Total Collected")
        self.city_tree.heading("total_pending", text="Total Pending")
        self.city_tree.heading("late_invoice_count", text="Late Invoices")

        self.city_tree.column("city", width=120)
        self.city_tree.column("total_invoiced", width=130, anchor="e")
        self.city_tree.column("total_collected", width=130, anchor="e")
        self.city_tree.column("total_pending", width=130, anchor="e")
        self.city_tree.column("late_invoice_count", width=100, anchor="center")

        self.city_tree.pack(side="left", fill="both", expand=True)

        city_scroll = ttk.Scrollbar(city_frame, orient="vertical", command=self.city_tree.yview)
        self.city_tree.configure(yscrollcommand=city_scroll.set)
        city_scroll.pack(side="right", fill="y")

        late_frame = ttk.LabelFrame(self.report_tab, text="Late Payment Alerts", padding=12)
        late_frame.pack(fill="both", expand=True)

        late_columns = ("invoiceID", "tenant_name", "city", "due_date", "amount_due", "outstanding_balance")
        self.late_tree = ttk.Treeview(late_frame, columns=late_columns, show="headings", height=8)

        self.late_tree.heading("invoiceID", text="Invoice ID")
        self.late_tree.heading("tenant_name", text="Tenant")
        self.late_tree.heading("city", text="City")
        self.late_tree.heading("due_date", text="Due Date")
        self.late_tree.heading("amount_due", text="Amount Due")
        self.late_tree.heading("outstanding_balance", text="Outstanding")

        self.late_tree.column("invoiceID", width=90, anchor="center")
        self.late_tree.column("tenant_name", width=160)
        self.late_tree.column("city", width=120)
        self.late_tree.column("due_date", width=100, anchor="center")
        self.late_tree.column("amount_due", width=100, anchor="e")
        self.late_tree.column("outstanding_balance", width=110, anchor="e")

        self.late_tree.pack(side="left", fill="both", expand=True)

        late_scroll = ttk.Scrollbar(late_frame, orient="vertical", command=self.late_tree.yview)
        self.late_tree.configure(yscrollcommand=late_scroll.set)
        late_scroll.pack(side="right", fill="y")
        # =========================
    # REFRESH EVERYTHING
    # =========================
    def refresh_all(self):
        """
        Refresh all dashboard data.
        """
        self._load_lease_options()
        self._load_invoice_table()
        self._load_open_invoice_options()
        self._load_payment_table()
        self._load_reports()

    # =========================
    # LOAD LEASE OPTIONS
    # =========================
    def _load_lease_options(self):
        """
        Load active leases into invoice generation combobox.
        """
        self.lease_map.clear()

        leases = LeaseDAO.get_all_leases_with_financial_details()
        active_leases = [lease for lease in leases if str(lease.get("status", "")).lower() == "active"]

        values = []
        for lease in active_leases:
            label = (
                f"Lease #{lease['leaseID']} | "
                f"{lease['tenant_name']} | "
                f"{lease['apartment_type']} | "
                f"{lease.get('city', 'Unknown')} | "
                f"Rent: {float(lease['rent']):.2f}"
            )
            self.lease_map[label] = lease
            values.append(label)

        self.lease_combo["values"] = values

        if values:
            self.lease_combo.current(0)
            self._on_lease_selected()
        else:
            self.lease_combo.set("")
            self.billing_start_var.set("")
            self.billing_end_var.set("")
            self.invoice_due_var.set("")
            self.amount_due_var.set("")

    # =========================
    # LOAD INVOICE TABLE
    # =========================
    def _load_invoice_table(self):
        """
        Load invoices into the invoice treeview.
        """
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)

        InvoiceDAO.mark_overdue_invoices()
        invoices = InvoiceDAO.get_all_invoices()

        for inv in invoices:
            period = f"{inv['billing_period_start']} to {inv['billing_period_end']}"
            self.invoice_tree.insert(
                "",
                "end",
                values=(
                    inv["invoiceID"],
                    inv["tenant_name"],
                    inv.get("city", "Unknown"),
                    period,
                    inv["due_date"],
                    f"{float(inv['amount_due']):.2f}",
                    inv["status"]
                )
            )

    # =========================
    # LOAD OPEN INVOICE OPTIONS
    # =========================
    def _load_open_invoice_options(self):
        """
        Load unpaid / partial / late invoices into payment combobox.
        """
        self.invoice_map.clear()

        InvoiceDAO.mark_overdue_invoices()
        open_invoices = InvoiceDAO.get_open_invoices()

        values = []
        for inv in open_invoices:
            outstanding = InvoiceDAO.get_outstanding_balance(inv["invoiceID"])
            label = (
                f"Invoice #{inv['invoiceID']} | "
                f"{inv['tenant_name']} | "
                f"{inv.get('city', 'Unknown')} | "
                f"Outstanding: {outstanding:.2f} | "
                f"Status: {inv['status']}"
            )
            self.invoice_map[label] = inv
            values.append(label)

        self.open_invoice_combo["values"] = values

        if values:
            self.open_invoice_combo.current(0)
            self._on_invoice_selected_for_payment()
        else:
            self.open_invoice_combo.set("")
            self.amount_paid_var.set("")

    # =========================
    # LOAD PAYMENT TABLE
    # =========================
    def _load_payment_table(self):
        """
        Load payment history into the payment treeview.
        """
        for item in self.payment_tree.get_children():
            self.payment_tree.delete(item)

        payments = PaymentDAO.get_all_payments()

        for pay in payments:
            self.payment_tree.insert(
                "",
                "end",
                values=(
                    pay["paymentID"],
                    pay["tenant_name"],
                    pay.get("city", "Unknown"),
                    pay["payment_date"],
                    f"{float(pay['amount_paid']):.2f}",
                    pay["payment_method"],
                    pay["receipt_number"]
                )
            )

    # =========================
    # LOAD REPORTS
    # =========================
    def _load_reports(self):
        """
        Refresh summary values and report tables.
        """
        summary = ReportDAO.get_overall_financial_summary()
        self.total_invoiced_var.set(f"{float(summary['total_invoiced']):.2f}")
        self.total_collected_var.set(f"{float(summary['total_collected']):.2f}")
        self.total_pending_var.set(f"{float(summary['total_pending']):.2f}")
        self.late_invoice_count_var.set(str(summary["late_invoice_count"]))

        for item in self.city_tree.get_children():
            self.city_tree.delete(item)

        city_rows = ReportDAO.get_financial_summary_by_city()
        for row in city_rows:
            self.city_tree.insert(
                "",
                "end",
                values=(
                    row["city"],
                    f"{float(row['total_invoiced']):.2f}",
                    f"{float(row['total_collected']):.2f}",
                    f"{float(row['total_pending']):.2f}",
                    row["late_invoice_count"]
                )
            )

        for item in self.late_tree.get_children():
            self.late_tree.delete(item)

        late_rows = ReportDAO.get_late_invoices()
        for row in late_rows:
            self.late_tree.insert(
                "",
                "end",
                values=(
                    row["invoiceID"],
                    row["tenant_name"],
                    row["city"],
                    row["due_date"],
                    f"{float(row['amount_due']):.2f}",
                    f"{float(row['outstanding_balance']):.2f}"
                )
            )

    # =========================
    # LEASE SELECTION HANDLER
    # =========================
    def _on_lease_selected(self, event=None):
        """
        When a lease is selected, pre-fill amount and suggested dates.
        """
        selected = self.lease_combo.get()
        lease = self.lease_map.get(selected)

        if not lease:
            return

        self.amount_due_var.set(f"{float(lease['rent']):.2f}")

        today = date.today()
        start_of_month = today.replace(day=1)
        next_month = (start_of_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_of_month = next_month - timedelta(days=1)

        self.billing_start_var.set(start_of_month.isoformat())
        self.billing_end_var.set(end_of_month.isoformat())

        due_date_value = end_of_month + timedelta(days=7)
        self.invoice_due_var.set(due_date_value.isoformat())

    # =========================
    # CREATE INVOICE
    # =========================
    def create_invoice(self):
        """
        Generate a new invoice for the selected lease.
        """
        selected = self.lease_combo.get()
        lease = self.lease_map.get(selected)

        if not lease:
            messagebox.showerror("Error", "Please select a lease.")
            return

        lease_id = lease["leaseID"]
        billing_start = self.billing_start_var.get().strip()
        billing_end = self.billing_end_var.get().strip()
        due_date_value = self.invoice_due_var.get().strip()
        amount_due_text = self.amount_due_var.get().strip()

        if not billing_start or not billing_end or not due_date_value or not amount_due_text:
            messagebox.showerror("Error", "Please complete all invoice fields.")
            return

        try:
            datetime.strptime(billing_start, "%Y-%m-%d")
            datetime.strptime(billing_end, "%Y-%m-%d")
            datetime.strptime(due_date_value, "%Y-%m-%d")
            amount_due = float(amount_due_text)
        except ValueError:
            messagebox.showerror("Error", "Invalid date or amount format.")
            return

        if amount_due <= 0:
            messagebox.showerror("Error", "Amount due must be greater than 0.")
            return

        if InvoiceDAO.invoice_exists_for_period(lease_id, billing_start, billing_end):
            messagebox.showwarning(
                "Duplicate Invoice",
                "An invoice already exists for this lease and billing period."
            )
            return

        invoice_id = InvoiceDAO.create_invoice(
            leaseID=lease_id,
            billing_period_start=billing_start,
            billing_period_end=billing_end,
            due_date=due_date_value,
            amount_due=amount_due
        )

        messagebox.showinfo("Success", f"Invoice #{invoice_id} created successfully.")
        self.refresh_all()

    # =========================
    # OPEN INVOICE SELECTION HANDLER
    # =========================
    def _on_invoice_selected_for_payment(self, event=None):
        """
        Auto-fill amount paid with the current outstanding balance.
        """
        selected = self.open_invoice_combo.get()
        invoice = self.invoice_map.get(selected)

        if not invoice:
            self.amount_paid_var.set("")
            return

        outstanding = InvoiceDAO.get_outstanding_balance(invoice["invoiceID"])
        self.amount_paid_var.set(f"{outstanding:.2f}")

    # =========================
    # RECORD PAYMENT
    # =========================
    def record_payment(self):
        """
        Record payment for the selected invoice and show a receipt.
        """
        selected = self.open_invoice_combo.get()
        invoice = self.invoice_map.get(selected)

        if not invoice:
            messagebox.showerror("Error", "Please select an open invoice.")
            return

        payment_date_value = self.payment_date_var.get().strip()
        amount_paid_text = self.amount_paid_var.get().strip()
        payment_method = self.payment_method_combo.get().strip() or "MANUAL"

        try:
            datetime.strptime(payment_date_value, "%Y-%m-%d")
            amount_paid = float(amount_paid_text)
        except ValueError:
            messagebox.showerror("Error", "Invalid payment date or amount.")
            return

        if amount_paid <= 0:
            messagebox.showerror("Error", "Payment amount must be greater than 0.")
            return

        invoice_id = invoice["invoiceID"]
        outstanding = InvoiceDAO.get_outstanding_balance(invoice_id)

        if amount_paid > outstanding:
            confirm = messagebox.askyesno(
                "Overpayment Warning",
                f"Outstanding balance is {outstanding:.2f}.\n"
                f"You entered {amount_paid:.2f}.\n\n"
                f"Do you want to continue?"
            )
            if not confirm:
                return

        payment_id = PaymentDAO.create_payment(
            invoiceID=invoice_id,
            payment_date=payment_date_value,
            amount_paid=amount_paid,
            payment_method=payment_method
        )

        messagebox.showinfo("Success", f"Payment #{payment_id} recorded successfully.")
        self.refresh_all()
        self._show_receipt_popup(payment_id)

    # =========================
    # RECEIPT POPUP
    # =========================
    def _show_receipt_popup(self, payment_id):
        """
        Show a simple receipt popup after payment is recorded.
        """
        receipt = PaymentDAO.get_receipt_data(payment_id)
        if not receipt:
            return

        popup = tk.Toplevel(self)
        popup.title("Payment Receipt")
        popup.geometry("540x540")
        popup.transient(self)
        popup.grab_set()

        frame = ttk.Frame(popup, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Receipt",
            font=("Arial", 18, "bold")
        ).pack(anchor="center", pady=(0, 12))

        receipt_lines = [
            f"Receipt Number: {receipt['receipt_number']}",
            f"Payment ID: {receipt['paymentID']}",
            f"Invoice ID: {receipt['invoiceID']}",
            f"Lease ID: {receipt['leaseID']}",
            "",
            f"Tenant: {receipt['tenant_name']}",
            f"Apartment: {receipt['apartment_type']}",
            f"City: {receipt.get('city', 'Unknown')}",
            "",
            f"Billing Period: {receipt['billing_period_start']} to {receipt['billing_period_end']}",
            f"Invoice Due Date: {receipt['due_date']}",
            f"Invoice Amount Due: {float(receipt['amount_due']):.2f}",
            f"Invoice Status: {receipt['invoice_status']}",
            "",
            f"Payment Date: {receipt['payment_date']}",
            f"Amount Paid: {float(receipt['amount_paid']):.2f}",
            f"Payment Method: {receipt['payment_method']}",
        ]

        text = tk.Text(frame, wrap="word", height=20, width=62)
        text.pack(fill="both", expand=True)
        text.insert("1.0", "\n".join(receipt_lines))
        text.config(state="disabled")

        ttk.Button(frame, text="Close", command=popup.destroy).pack(pady=(12, 0))
    # =========================
    # CSV exports 
    # =========================
    def export_reports_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Finance Report as CSV"
        )
        if not path:
            return

        summary = ReportDAO.get_overall_financial_summary()
        city_rows = ReportDAO.get_financial_summary_by_city()
        late_rows = ReportDAO.get_late_invoices()

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(["OVERALL FINANCIAL SUMMARY"])
            writer.writerow(["Total Invoiced", summary["total_invoiced"]])
            writer.writerow(["Total Collected", summary["total_collected"]])
            writer.writerow(["Total Pending", summary["total_pending"]])
            writer.writerow(["Late Invoices", summary["late_invoice_count"]])
            writer.writerow([])

            writer.writerow(["FINANCIAL SUMMARY BY CITY"])
            writer.writerow(["City", "Total Invoiced", "Total Collected", "Total Pending", "Late Invoices"])
            for row in city_rows:
                writer.writerow([
                    row["city"],
                    row["total_invoiced"],
                    row["total_collected"],
                    row["total_pending"],
                    row["late_invoice_count"],
                ])
            writer.writerow([])

            writer.writerow(["LATE PAYMENT ALERTS"])
            writer.writerow(["Invoice ID", "Tenant", "City", "Due Date", "Amount Due", "Outstanding Balance"])
            for row in late_rows:
                writer.writerow([
                    row["invoiceID"],
                    row["tenant_name"],
                    row["city"],
                    row["due_date"],
                    row["amount_due"],
                    row["outstanding_balance"],
                ])

        messagebox.showinfo("Export Complete", f"CSV report saved to:\n{path}")
    # =========================
    # PDF exports 
    # =========================
    def export_reports_pdf(self):
        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror(
                "Missing Package",
                "PDF export needs fpdf2.\n\nInstall it with:\npip install fpdf2"
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Finance Report as PDF"
        )
        if not path:
            return

        summary = ReportDAO.get_overall_financial_summary()
        city_rows = ReportDAO.get_financial_summary_by_city()
        late_rows = ReportDAO.get_late_invoices()

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Finance Report", ln=True)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Overall Financial Summary", ln=True)

        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"Total Invoiced: {summary['total_invoiced']:.2f}", ln=True)
        pdf.cell(0, 8, f"Total Collected: {summary['total_collected']:.2f}", ln=True)
        pdf.cell(0, 8, f"Total Pending: {summary['total_pending']:.2f}", ln=True)
        pdf.cell(0, 8, f"Late Invoices: {summary['late_invoice_count']}", ln=True)
        pdf.ln(4)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Financial Summary by City", ln=True)

        pdf.set_font("Arial", size=10)
        for row in city_rows:
            pdf.cell(
                0,
                7,
                f"{row['city']} | Invoiced: {row['total_invoiced']:.2f} | "
                f"Collected: {row['total_collected']:.2f} | "
                f"Pending: {row['total_pending']:.2f} | "
                f"Late: {row['late_invoice_count']}",
                ln=True
            )

        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Late Payment Alerts", ln=True)

        pdf.set_font("Arial", size=10)
        if not late_rows:
            pdf.cell(0, 7, "No late invoices.", ln=True)
        else:
            for row in late_rows:
                pdf.multi_cell(
                    0,
                    7,
                    f"Invoice #{row['invoiceID']} | {row['tenant_name']} | {row['city']} | "
                    f"Due: {row['due_date']} | Amount Due: {row['amount_due']:.2f} | "
                    f"Outstanding: {row['outstanding_balance']:.2f}"
                )

        pdf.output(path)
        messagebox.showinfo("Export Complete", f"PDF report saved to:\n{path}")
    
    def export_selected_invoice_pdf(self):
        selected = self.invoice_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an invoice first.")
            return

        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror(
                "Missing Package",
                "PDF export needs fpdf2.\n\nInstall it with:\npip install fpdf2"
            )
            return

        invoice_id = int(self.invoice_tree.item(selected[0], "values")[0])
        invoice = InvoiceDAO.get_invoice_by_id(invoice_id)

        if not invoice:
            messagebox.showerror("Error", "Invoice record not found.")
            return

        total_paid = InvoiceDAO.get_total_paid_for_invoice(invoice_id)
        outstanding = InvoiceDAO.get_outstanding_balance(invoice_id)

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Invoice PDF"
        )
        if not path:
            return

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Invoice #{invoice_id}", ln=True)

        pdf.set_font("Arial", size=11)
        lines = [
            f"Tenant: {invoice.get('tenant_name', 'N/A')}",
            f"Apartment: {invoice.get('apartment_type', 'N/A')}",
            f"City: {invoice.get('city', 'Unknown')}",
            "",
            f"Billing Period: {invoice.get('billing_period_start', '')} to {invoice.get('billing_period_end', '')}",
            f"Due Date: {invoice.get('due_date', '')}",
            f"Amount Due: {float(invoice.get('amount_due', 0)):.2f}",
            f"Total Paid: {float(total_paid):.2f}",
            f"Outstanding Balance: {float(outstanding):.2f}",
            f"Status: {invoice.get('status', 'N/A')}",
        ]

        for line in lines:
            pdf.cell(0, 8, line, ln=True)

        pdf.output(path)
        messagebox.showinfo("Export Complete", f"Invoice PDF saved to:\n{path}")

    def export_selected_payment_pdf(self):
        selected = self.payment_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a payment first.")
            return

        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror(
                "Missing Package",
                "PDF export needs fpdf2.\n\nInstall it with:\npip install fpdf2"
            )
            return

        payment_id = int(self.payment_tree.item(selected[0], "values")[0])
        receipt = PaymentDAO.get_receipt_data(payment_id)

        if not receipt:
            messagebox.showerror("Error", "Payment record not found.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Payment Receipt PDF"
        )
        if not path:
            return

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Receipt #{receipt.get('receipt_number', payment_id)}", ln=True)

        pdf.set_font("Arial", size=11)
        lines = [
            f"Payment ID: {receipt.get('paymentID', '')}",
            f"Invoice ID: {receipt.get('invoiceID', '')}",
            f"Lease ID: {receipt.get('leaseID', '')}",
            "",
            f"Tenant: {receipt.get('tenant_name', 'N/A')}",
            f"Apartment: {receipt.get('apartment_type', 'N/A')}",
            f"City: {receipt.get('city', 'Unknown')}",
            "",
            f"Billing Period: {receipt.get('billing_period_start', '')} to {receipt.get('billing_period_end', '')}",
            f"Invoice Due Date: {receipt.get('due_date', '')}",
            f"Invoice Amount Due: {float(receipt.get('amount_due', 0)):.2f}",
            f"Invoice Status: {receipt.get('invoice_status', 'N/A')}",
            "",
            f"Payment Date: {receipt.get('payment_date', '')}",
            f"Amount Paid: {float(receipt.get('amount_paid', 0)):.2f}",
            f"Payment Method: {receipt.get('payment_method', 'N/A')}",
        ]

        for line in lines:
            pdf.cell(0, 8, line, ln=True)

        pdf.output(path)
        messagebox.showinfo("Export Complete", f"Receipt PDF saved to:\n{path}")