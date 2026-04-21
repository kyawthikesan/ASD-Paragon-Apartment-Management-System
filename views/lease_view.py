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

        # TABLE
        table_frame = ttk.LabelFrame(main_frame, text="Leases", padding=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "Tenant", "Apartment", "Start", "End", "Status")

        self.table = ttk.Treeview(table_frame, columns=columns, show="headings")

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
            
    def clear_fields(self):
        self.tenant_combo.set("")
        self.apartment_combo.set("")

        # reset dates properly
        self.start.set_date(self.start.get_date())
        self.end.set_date(self.start.get_date() + timedelta(days=365))

    
