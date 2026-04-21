import tkinter as tk
from tkinter import messagebox, ttk
from controllers.tenant_controller import TenantController
from controllers.auth_controller import AuthController
from views.premium_shell import PremiumAppShell


class TenantView(tk.Frame):

    def __init__(self, parent, back_callback):
        super().__init__(parent, bg="#F9F5EE")
        self.pack(fill="both", expand=True)
        self.city_scope = AuthController.get_city_scope()
        role = AuthController.get_current_role()
        nav_sections = [
            {"title": "Overview", "items": [{"label": "Dashboard", "action": back_callback, "icon": "⌂"}]},
            {
                "title": "Management",
                "items": [
                    {"label": "Tenants", "action": lambda: None, "icon": "👤", "badge": None},
                ],
            },
        ]
        if AuthController.can_access_feature("apartment_management", role):
            nav_sections[1]["items"].append({"label": "Apartments", "action": back_callback, "icon": "▦"})
        if AuthController.can_access_feature("lease_management", role):
            nav_sections[1]["items"].append({"label": "Leases", "action": back_callback, "icon": "📄"})

        shell = PremiumAppShell(
            self,
            page_title="Tenant Management",
            on_logout=back_callback,
            active_nav="Tenants",
            nav_sections=nav_sections,
            footer_action_label="Back to Dashboard",
            search_placeholder="Search tenants...",
        )
        content = shell.content

        summary = tk.Frame(content, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E4D8C6", padx=14, pady=10)
        summary.pack(fill="x", pady=(0, 10))
        tk.Label(summary, text="Register New Tenant", bg="#FFFFFF", fg="#2F2A23", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(summary, text="Add and manage tenant details for current office", bg="#FFFFFF", fg="#7A6F61", font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        form_frame = ttk.LabelFrame(content, text="Tenant Details", padding=15)
        form_frame.pack(fill="x", pady=(0, 10))

        # Name
        ttk.Label(form_frame, text="Name").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.name = ttk.Entry(form_frame, width=30)
        self.name.grid(row=0, column=1, padx=10, pady=5)

        # NI Number
        ttk.Label(form_frame, text="NI Number").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.NI_number = ttk.Entry(form_frame, width=30)
        self.NI_number.grid(row=1, column=1, padx=10, pady=5)
        self.NI_number.bind("<KeyRelease>", self.uppercase_ni)

        # Phone
        ttk.Label(form_frame, text="Phone").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        vcmd = (self.register(self.validate_phone), "%P")
        self.phone = ttk.Entry(form_frame, validate="key", validatecommand=vcmd, width=30)
        self.phone.grid(row=2, column=1, padx=10, pady=5)

        # Email
        ttk.Label(form_frame, text="Email").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.email = ttk.Entry(form_frame, width=30)
        self.email.grid(row=3, column=1, padx=10, pady=5)

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="Add", command=self.add_tenant).grid(row=0, column=0, padx=5)

        self.update_btn = ttk.Button(button_frame, text="Update", command=self.update_tenant, state="disabled")
        self.update_btn.grid(row=0, column=1, padx=5)

        self.delete_btn = ttk.Button(button_frame, text="Delete", command=self.delete_tenant, state="disabled")
        self.delete_btn.grid(row=0, column=2, padx=5)


        table_frame = ttk.LabelFrame(content, text="Tenant List", padding=10)
        table_frame.pack(fill="both", expand=True, pady=10)

        # 🔍 SEARCH BAR
        search_frame = ttk.Frame(table_frame)
        search_frame.pack(fill="x", pady=5)

        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)

        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)

        ttk.Button(search_frame, text="Search", command=self.search_tenant).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Show All", command=self.load_tenants).pack(side="left", padx=5)


        # 📦 TABLE CONTAINER (IMPORTANT)
        table_container = ttk.Frame(table_frame)
        table_container.pack(fill="both", expand=True)

        columns = ("ID", "Name", "NI Number", "Phone", "Email", "Lease Status")

        self.table = ttk.Treeview(table_container, columns=columns, show="headings")

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=140, anchor="center", stretch=True)
            self.table.tag_configure("odd", background="#f9f9f9")
            self.table.tag_configure("even", background="#ffffff")
            self.table.tag_configure("active", foreground="green")
            self.table.tag_configure("ended", foreground="red")
            self.table.tag_configure("no_lease", foreground="gray")
            

        # table
        self.table.pack(side="left", fill="both", expand=True)

        # scrollbar
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.table.yview)
        scrollbar.pack(side="right", fill="y")

        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.bind("<<TreeviewSelect>>", self.fill_fields)

        self.load_tenants()

    # ======================
    # LOAD DATA
    # ======================
    def load_tenants(self):
        for row in self.table.get_children():
            self.table.delete(row)

        tenants = TenantController.get_all_tenants(city=self.city_scope)

        for i, tenant in enumerate(tenants):
            self.insert_tenant_row(tenant, i)

    # ======================
    # FILL FORM
    # ======================
    def fill_fields(self, event):
        selected = self.table.selection()
        if not selected:
            return

        values = self.table.item(selected[0], "values")

        self.name.delete(0, tk.END)
        self.name.insert(0, values[1])

        self.NI_number.delete(0, tk.END)
        self.NI_number.insert(0, values[2])

        self.phone.delete(0, tk.END)
        self.phone.insert(0, values[3])

        self.email.delete(0, tk.END)
        self.email.insert(0, values[4])

        # Enable buttons
        self.update_btn.config(state="normal")
        self.delete_btn.config(state="normal")

    # ======================
    # VALIDATION
    # ======================
    def validate_phone(self, P):
        return P.isdigit() or P == ""

    def uppercase_ni(self, event):
        current = self.NI_number.get()
        self.NI_number.delete(0, tk.END)
        self.NI_number.insert(0, current.upper())
        self.NI_number.icursor(tk.END)

    # ======================
    # CRUD
    # ======================
    def add_tenant(self):
        name = self.name.get()
        NI_number = self.NI_number.get()
        phone = self.phone.get()
        email = self.email.get()

        if not name or not NI_number or not phone:
            messagebox.showerror("Error", "Name, NI Number and Phone are required")
            return

        TenantController.add_tenant(name, NI_number, phone, email)
        messagebox.showinfo("Success", "Tenant Added")

        self.load_tenants()
        self.clear_fields()

    def delete_tenant(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a tenant")
            return

        tenant_id = self.table.item(selected[0], "values")[0]

        TenantController.delete_tenant(tenant_id)
        messagebox.showinfo("Success", "Tenant deleted")

        self.load_tenants()
        self.clear_fields()

    def update_tenant(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a tenant")
            return

        tenant_id = self.table.item(selected[0], "values")[0]

        name = self.name.get()
        NI_number = self.NI_number.get()
        phone = self.phone.get()
        email = self.email.get()

        TenantController.update_tenant(tenant_id, name, NI_number, phone, email)
        messagebox.showinfo("Success", "Tenant updated")

        self.load_tenants()
        self.clear_fields()

    # ======================
    # CLEAR
    # ======================
    def clear_fields(self):
        self.name.delete(0, tk.END)
        self.NI_number.delete(0, tk.END)
        self.phone.delete(0, tk.END)
        self.email.delete(0, tk.END)

        self.update_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")

    def search_tenant(self):
        keyword = self.search_entry.get()
        if hasattr(TenantController, "search_tenant"):
            tenants = TenantController.search_tenant(keyword)
        else:
            # Fallback keeps the search button usable even if the controller lacks helper.
            keyword_l = keyword.strip().lower()
            tenants = [
                row for row in TenantController.get_all_tenants(city=self.city_scope)
                if keyword_l in str(row["name"]).lower()
                or keyword_l in str(row["NI_number"]).lower()
                or keyword_l in str(row["phone"]).lower()
                or keyword_l in str(row["email"]).lower()
            ]

        for row in self.table.get_children():
            self.table.delete(row)

        for i, tenant in enumerate(tenants):
            self.insert_tenant_row(tenant, i)

    def insert_tenant_row(self, tenant, i):
        base_tag = "even" if i % 2 == 0 else "odd"

        status = tenant["lease_status"]

        if status == "Active":
            display_status = "🟢 Active"
            status_tag = "active"
        elif status == "Ended":
            display_status = "🔴 Ended"
            status_tag = "ended"
        else:
            display_status = "⚪ No Lease"
            status_tag = "no_lease"

        self.table.insert("", tk.END, values=(
            tenant["tenantID"],
            tenant["name"],
            tenant["NI_number"],
            tenant["phone"],
            tenant["email"],
            display_status
        ), tags=(base_tag, status_tag))

    
