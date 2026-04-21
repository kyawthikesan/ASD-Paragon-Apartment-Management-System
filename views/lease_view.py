import tkinter as tk
from tkinter import ttk, messagebox
from controllers.lease_controller import LeaseController
from tkcalendar import DateEntry
from datetime import timedelta
from dao.apartment_dao import ApartmentDAO
from dao.tenant_dao import TenantDAO
from dao.lease_dao import LeaseDAO
from controllers.auth_controller import AuthController

class LeaseView(tk.Frame):

    def __init__(self, parent, back_callback):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.city_scope = AuthController.get_city_scope()

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)

        # Top
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x")

        ttk.Button(top_frame, text="← Back", command=back_callback).pack(side="left")
        ttk.Label(top_frame, text="Lease Management", font=("Arial", 16, "bold")).pack(side="left", padx=20)

        # FORM
        form_frame = ttk.LabelFrame(main_frame, text="Lease Details", padding=15)
        form_frame.pack(fill="x", pady=10)

        ttk.Label(form_frame, text="Tenant ID").grid(row=0, column=0, padx=10, pady=5)
        self.tenant_combo = ttk.Combobox(form_frame, state="readonly")
        self.tenant_combo.grid(row=0, column=1)
        self.load_tenants()

        ttk.Label(form_frame, text="Apartment").grid(row=1, column=0, padx=10, pady=5)
        self.apartment_combo = ttk.Combobox(form_frame, state="readonly")
        self.apartment_combo.grid(row=1, column=1)
        self.load_available_apartments()

        ttk.Label(form_frame, text="Start Date").grid(row=2, column=0, padx=10, pady=5)
        self.start = DateEntry(form_frame, date_pattern='yyyy-mm-dd')
        self.start.grid(row=2, column=1)

        ttk.Label(form_frame, text="End Date").grid(row=3, column=0, padx=10, pady=5)
        self.end = DateEntry(form_frame, date_pattern='yyyy-mm-dd')
        self.end.grid(row=3, column=1)

        self.end.set_date(self.start.get_date() + timedelta(days=365))

        def update_dates(event):
            start = self.start.get_date()

            self.end.config(mindate=start)
            self.end.set_date(start + timedelta(days=365))

        self.start.bind("<<DateEntrySelected>>", update_dates)

        ttk.Button(form_frame, text="Create Lease", command=self.create_lease)\
            .grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(form_frame, text="Terminate Lease", command=self.terminate_lease)\
            .grid(row=5, column=0, columnspan=2, pady=5)

        # TABLE
        table_frame = ttk.LabelFrame(main_frame, text="Leases", padding=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "Tenant", "Apartment", "Start", "End", "Status")

        self.table = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.table.bind("<<TreeviewSelect>>", self.select_lease)

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=140, stretch=True, anchor="center")

        self.table.pack(fill="both", expand=True)

        self.load_leases()

    def load_available_apartments(self):
        apartments = ApartmentDAO.get_available_apartments(city=self.city_scope)

        self.apartment_map = {
            f"{apt['city']} - {apt['type']} (#{apt['apartmentID']})": apt["apartmentID"]
            for apt in apartments
        }

        self.apartment_combo["values"] = list(self.apartment_map.keys())

        if apartments:
            self.apartment_combo.current(0)

    def load_tenants(self):
        tenants = TenantDAO.get_all_tenants()

        self.tenant_map = {
            f"{t['name']} (#{t['tenantID']})": t["tenantID"]
            for t in tenants
        }

        self.tenant_combo["values"] = list(self.tenant_map.keys())

        if tenants:
            self.tenant_combo.current(0)

    def create_lease(self):
        selected_tenant = self.tenant_combo.get()
        tenant_id = self.tenant_map[selected_tenant]

        selected = self.apartment_combo.get()
        apartment_id = self.apartment_map[selected]

        result = LeaseController.create_lease(
            tenant_id,
            apartment_id,
            self.start.get(),
            self.end.get()
        )

        if result == "Success":
            messagebox.showinfo("Success", "Lease created")
            self.load_leases()
            self.clear_fields()
            self.load_available_apartments()
        else:
            messagebox.showerror("Error", result)
        

    def load_leases(self):
        LeaseDAO.expire_leases()
        for row in self.table.get_children():
            self.table.delete(row)

        leases = LeaseController.get_all_leases(city=self.city_scope)

        for lease in leases:
            self.table.insert("", tk.END, values=(
                lease["leaseID"],
                lease["tenant"],
                lease["apartment"],
                lease["start_date"],
                lease["end_date"],
                lease["status"]
            ))

    def select_lease(self, event):
        selected = self.table.selection()
        if not selected:
            return

        values = self.table.item(selected[0], "values")

        self.selected_lease_id = values[0]
        self.selected_tenant = values[1]
        self.selected_apartment = values[2]
        self.selected_start = values[3]
        self.selected_end = values[4]
        self.selected_status = values[5]

    def terminate_lease(self):
        if not hasattr(self, "selected_lease_id"):
            messagebox.showerror("Error", "Please select a lease")
            return

        self.open_termination_window()
            
    def open_termination_window(self):
        window = tk.Toplevel(self)
        window.title("Terminate Lease")
        window.after(10, lambda: self.center_window(window, 400, 450))
        window.resizable(False, False)

        ttk.Label(window, text="Lease Termination", font=("Arial", 14, "bold")).pack(pady=10)

        ttk.Label(window, text="⚠ Early Termination Policy", font=("Arial", 10, "bold")).pack(pady=5)

        ttk.Label(window, text="• 1 month notice required").pack()
        ttk.Label(window, text="• 5% penalty on monthly rent").pack()
        ttk.Label(window, text="• Lease will be ended immediately").pack()
        ttk.Label(window, text="• Apartment will become available").pack()

        ttk.Button(
            window,
            text="Confirm Termination",
            command=lambda: self.confirm_termination(window)
        ).pack(pady=20)

        ttk.Button(
            window,
            text="Cancel",
            command=window.destroy
        ).pack()        

    def confirm_termination(self, window):
        penalty = LeaseDAO.terminate_lease(self.selected_lease_id)

        window.destroy()

        self.show_termination_record(penalty)

        self.load_leases()
        self.load_available_apartments()

    def show_termination_record(self, penalty):
        record = tk.Toplevel(self)
        record.title("Lease Termination Record")
        record.after(10, lambda: self.center_window(record, 400, 450))
        record.resizable(False, False)

        ttk.Label(record, text="Lease Termination Record", font=("Arial", 14, "bold")).pack(pady=10)

        ttk.Separator(record).pack(fill="x", padx=10, pady=5)

        ttk.Label(record, text=f"Lease ID: {self.selected_lease_id}").pack(pady=5)
        ttk.Label(record, text=f"Tenant: {self.selected_tenant}").pack(pady=5)
        ttk.Label(record, text=f"Apartment: {self.selected_apartment}").pack(pady=5)

        ttk.Label(record, text=f"Start Date: {self.selected_start}").pack(pady=5)
        ttk.Label(record, text=f"End Date: {self.selected_end}").pack(pady=5)

        today = date.today().isoformat()
        ttk.Label(record, text=f"Termination Date: {today}").pack(pady=5)

        ttk.Label(record, text=f"Penalty Charged: £{penalty:.2f}").pack(pady=5)

        status_text = "Early Termination" if penalty > 0 else "Contract Completed"
        ttk.Label(record, text=f"Termination Type: {status_text}").pack(pady=5)

        ttk.Separator(record).pack(fill="x", padx=10, pady=10)

        ttk.Label(record, text="✔ Lease status updated to 'Ended'").pack(pady=3)
        ttk.Label(record, text="✔ Apartment marked as 'AVAILABLE'").pack(pady=3)

        ttk.Button(record, text="Close", command=record.destroy).pack(pady=15)

    def center_window(self, win, width=400, height=450):
        win.update_idletasks()

        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        win.geometry(f"{width}x{height}+{x}+{y}")

    def clear_fields(self):
        self.tenant_combo.set("")
        self.apartment_combo.set("")

        # reset dates properly
        self.start.set_date(self.start.get_date())
        self.end.set_date(self.start.get_date() + timedelta(days=365))

    
