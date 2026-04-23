# Student Name: Kyaw Thike (oliver) San
# Student ID: 25014001
# Module: UFCF8S-30-2 Advanced Software Development
import tkinter as tk
from tkinter import ttk, messagebox

from dao.maintenance_dao import MaintenanceDAO
from controllers.auth_controller import AuthController
from tkcalendar import DateEntry

class MaintenanceDashboardView(ttk.Frame):
    def __init__(
        self,
        parent,
        logout_callback=None,
        home_callback=None,
        open_tenant_management=None,
        open_apartment_management=None,
        open_lease_management=None,
        open_finance_payments=None,
        open_finance_reports=None,
        open_user_management=None,
        open_maintenance_dashboard=None,
        **_kwargs,
    ):
        super().__init__(parent)
        self.current_role = AuthController.get_current_role()
        self.pack(fill="both", expand=True)

        self.logout_callback = logout_callback
        self.home_callback = home_callback
        # Keep compatibility with newer router kwargs from main.py
        self.open_tenant_management = open_tenant_management
        self.open_apartment_management = open_apartment_management
        self.open_lease_management = open_lease_management
        self.open_finance_payments = open_finance_payments
        self.open_finance_reports = open_finance_reports
        self.open_user_management = open_user_management
        self.open_maintenance_dashboard = open_maintenance_dashboard
        self.dao = MaintenanceDAO()
        self.selected_request_id = None
        default_section = "create" if self.current_role == "front_desk" else "requests"
        self.active_section = tk.StringVar(value=default_section)

        self.tree = None
        self.priority_combo = None
        self.schedule_priority_var = tk.StringVar(value="Medium")

        # Safe shared state across sections
        self.selected_id_var = tk.StringVar(value="None")
        self.assigned_staff_var = tk.StringVar()
        self.scheduled_date_var = tk.StringVar()
        self.scheduled_time_var = tk.StringVar()
        self.hours_spent_var = tk.StringVar(value="0")
        self.cost_var = tk.StringVar(value="0")
        self.resolution_text = None

        self.priority_combo = None
        
        # =========================
        # Make the whole page scrollable
        # =========================
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # This is the real content frame where all widgets will be placed
        self.content = ttk.Frame(self.canvas)
        #splitting page 
        self.active_section = tk.StringVar(value="requests")
        self.content_window = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw"
        )

        # Update scroll area whenever content size changes
        self.content.bind("<Configure>", self._on_content_configure)

        # Keep inner frame width same as canvas width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._build_ui()
        self.load_data()

    def _on_content_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.content_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_ui(self):
        # =========================
        # Top header bar
        # =========================
        top_bar = ttk.Frame(self.content, padding=12)
        top_bar.pack(fill="x")

        ttk.Label(
            top_bar,
            text="Maintenance Dashboard",
            font=("Arial", 18, "bold")
        ).pack(side="left")

        if self.home_callback:
            ttk.Button(
                top_bar,
                text="Home",
                command=self.home_callback
            ).pack(side="right", padx=6)

        if self.logout_callback:
            ttk.Button(
                top_bar,
                text="Logout",
                command=self.logout_callback
            ).pack(side="right", padx=6)

        # =========================
        # Quick action buttons
        # =========================
        actions = ttk.Frame(self.content, padding=(12, 0, 12, 8))
        actions.pack(fill="x")

        ttk.Button(
            actions,
            text="Refresh",
            command=self.load_data
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            actions,
            text="Cost Report",
            command=self.show_report
        ).pack(side="left")

        # =========================
        # Section nav
        # =========================
        section_nav = ttk.Frame(self.content, padding=(12, 0, 12, 8))
        section_nav.pack(fill="x")

        if self.current_role in ("front_desk", "admin"):
            ttk.Button(
                section_nav,
                text="Create Maintenance Req",
                command=lambda: self.show_section("create")
            ).pack(side="left", padx=(0, 6))

        if self.current_role in ("front_desk", "maintenance", "admin", "manager"):
            ttk.Button(
                section_nav,
                text="Maintenance Req",
                command=lambda: self.show_section("requests")
            ).pack(side="left", padx=(0, 6))

        if self.current_role in ("maintenance", "admin"):
            ttk.Button(
                section_nav,
                text="Schedule / Update",
                command=lambda: self.show_section("schedule")
            ).pack(side="left", padx=(0, 6))

            ttk.Button(
                section_nav,
                text="Resolve",
                command=lambda: self.show_section("resolve")
            ).pack(side="left", padx=(0, 6))

        # =========================
        # Dynamic section container
        # =========================
        self.section_container = ttk.Frame(self.content, padding=(12, 0, 12, 12))
        self.section_container.pack(fill="both", expand=True)

        self.show_section(self.active_section.get())

    def show_section(self, section_name):
        self.active_section.set(section_name)

        for widget in self.section_container.winfo_children():
            widget.destroy()

        self.tree = None
        self.priority_combo = None
        self.resolution_text = None

        if section_name == "create":
            self._build_create_section(self.section_container)
        elif section_name == "requests":
            self._build_requests_section(self.section_container)
        elif section_name == "schedule":
            self._build_schedule_section(self.section_container)
        elif section_name == "resolve":
            self._build_resolve_section(self.section_container)

    def _build_create_section(self, parent):
        if self.current_role not in ("front_desk", "admin"):
            return

        create_frame = ttk.LabelFrame(
            parent,
            text="Create Maintenance Request",
            padding=12
        )
        create_frame.pack(fill="x", pady=(0, 12))

        ttk.Label(create_frame, text="Apartment ID").grid(
            row=0, column=0, sticky="w", padx=6, pady=6
        )
        self.create_apartment_id_var = tk.StringVar()
        ttk.Entry(
            create_frame,
            textvariable=self.create_apartment_id_var,
            width=22,
            state="readonly"
        ).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(create_frame, text="Tenant").grid(
            row=0, column=2, sticky="w", padx=6, pady=6
        )
        self.create_tenant_var = tk.StringVar()
        self.tenant_options = self.dao.get_tenant_options()

        self.tenant_dropdown = ttk.Combobox(
            create_frame,
            textvariable=self.create_tenant_var,
            state="readonly",
            width=30,
            values=[item["label"] for item in self.tenant_options]
        )
        self.tenant_dropdown.grid(row=0, column=3, sticky="w", padx=6, pady=6)
        self.tenant_dropdown.bind(
            "<<ComboboxSelected>>",
            self.auto_fill_apartment_from_tenant
        )

        ttk.Label(create_frame, text="Title").grid(
            row=1, column=0, sticky="w", padx=6, pady=6
        )
        self.create_title_var = tk.StringVar()
        ttk.Entry(
            create_frame,
            textvariable=self.create_title_var,
            width=50
        ).grid(row=1, column=1, columnspan=3, sticky="ew", padx=6, pady=6)

        ttk.Label(create_frame, text="Description").grid(
            row=2, column=0, sticky="nw", padx=6, pady=6
        )
        self.create_description_text = tk.Text(create_frame, width=58, height=4)
        self.create_description_text.grid(
            row=2, column=1, columnspan=3, sticky="ew", padx=6, pady=6
        )

        ttk.Label(create_frame, text="Priority").grid(
            row=3, column=0, sticky="w", padx=6, pady=6
        )
        self.create_priority_combo = ttk.Combobox(
            create_frame,
            state="readonly",
            values=["Low", "Medium", "High", "Urgent"],
            width=18
        )
        self.create_priority_combo.grid(
            row=3, column=1, sticky="w", padx=6, pady=6
        )
        self.create_priority_combo.set("Medium")

        ttk.Button(
            create_frame,
            text="Create Request",
            command=self.create_request
        ).grid(row=3, column=3, sticky="e", padx=6, pady=6)

        create_frame.columnconfigure(1, weight=1)
        create_frame.columnconfigure(2, weight=1)
        create_frame.columnconfigure(3, weight=1)

    def _build_requests_section(self, parent):
        table_frame = ttk.LabelFrame(parent, text="Maintenance Requests", padding=12)
        table_frame.pack(fill="both", expand=True)

        columns = (
            "requestID",
            "title",
            "priority",
            "status",
            "assigned_staff",
            "scheduled_date",
            "scheduled_time",
            "cost",
            "hours_spent",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12
        )

        self.tree.heading("requestID", text="Request ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("status", text="Status")
        self.tree.heading("assigned_staff", text="Assigned Staff")
        self.tree.heading("scheduled_date", text="Scheduled Date")
        self.tree.heading("scheduled_time", text="Time")
        self.tree.heading("cost", text="Cost")
        self.tree.heading("hours_spent", text="Hours")

        self.tree.column("requestID", width=90, anchor=tk.CENTER)
        self.tree.column("title", width=240, anchor=tk.W)
        self.tree.column("priority", width=95, anchor=tk.CENTER)
        self.tree.column("status", width=110, anchor=tk.CENTER)
        self.tree.column("assigned_staff", width=140, anchor=tk.W)
        self.tree.column("scheduled_date", width=110, anchor=tk.CENTER)
        self.tree.column("scheduled_time", width=90, anchor=tk.CENTER)
        self.tree.column("cost", width=90, anchor=tk.E)
        self.tree.column("hours_spent", width=90, anchor=tk.CENTER)

        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_request)
        action_bar = ttk.Frame(parent, padding=(0, 10, 0, 0))
        action_bar.pack(fill="x")

        if self.current_role in ("maintenance", "admin"):
            ttk.Button(
                action_bar,
                text="Schedule Selected",
                command=self.open_schedule_for_selected
            ).pack(side="left", padx=(0, 6))

            ttk.Button(
                action_bar,
                text="Resolve Selected",
                command=self.open_resolve_for_selected
            ).pack(side="left")
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.load_data()

    def open_schedule_for_selected(self):
        if not self.selected_request_id:
            messagebox.showwarning(
                "No Request Selected",
                "Please select a request from Maintenance Req first."
            )
            return

        self.show_section("schedule")

    def open_resolve_for_selected(self):
        if not self.selected_request_id:
            messagebox.showwarning(
                "No Request Selected",
                "Please select a request from Maintenance Req first."
            )
            return

        self.show_section("resolve")

    def _build_schedule_section(self, parent):
        if self.current_role not in ("maintenance", "admin"):
            return

        schedule_frame = ttk.LabelFrame(
            parent,
            text="Schedule / Update Request",
            padding=12
        )
        schedule_frame.pack(fill="x")

        ttk.Label(
            schedule_frame,
            text="Select a request first from 'Maintenance Req'."
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 10))

        ttk.Label(
            schedule_frame,
            text="Selected Request ID"
        ).grid(row=1, column=0, sticky="w", padx=6, pady=6)

        ttk.Label(
            schedule_frame,
            textvariable=self.selected_id_var
        ).grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(
            schedule_frame,
            text="Assigned Staff"
        ).grid(row=2, column=0, sticky="w", padx=6, pady=6)

        ttk.Entry(
            schedule_frame,
            textvariable=self.assigned_staff_var,
            width=24
        ).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(
            schedule_frame,
            text="Scheduled Date"
        ).grid(row=3, column=0, sticky="w", padx=6, pady=6)

        self.date_picker = DateEntry(
            schedule_frame,
            textvariable=self.scheduled_date_var,
            width=21,
            date_pattern="yyyy-mm-dd"
        )
        self.date_picker.grid(row=3, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(
            schedule_frame,
            text="Scheduled Time"
        ).grid(row=4, column=0, sticky="w", padx=6, pady=6)

        time_values = [
            f"{hour:02d}:{minute:02d}"
            for hour in range(24)
            for minute in (0, 15, 30, 45)
        ]

        self.time_combo = ttk.Combobox(
            schedule_frame,
            textvariable=self.scheduled_time_var,
            state="readonly",
            values=time_values,
            width=21
        )
        self.time_combo.grid(row=4, column=1, sticky="w", padx=6, pady=6)

        if not self.scheduled_time_var.get().strip():
            self.scheduled_time_var.set("09:00")

        ttk.Label(
            schedule_frame,
            text="Priority"
        ).grid(row=5, column=0, sticky="w", padx=6, pady=6)

        self.priority_combo = ttk.Combobox(
            schedule_frame,
            textvariable=self.schedule_priority_var,
            state="readonly",
            values=["Low", "Medium", "High", "Urgent"],
            width=21
        )
        self.priority_combo.grid(row=5, column=1, sticky="w", padx=6, pady=6)
        self.priority_combo.set(self.schedule_priority_var.get())

        ttk.Button(
            schedule_frame,
            text="Schedule Request",
            command=self.schedule_selected_request
        ).grid(row=6, column=1, sticky="w", padx=6, pady=(10, 0))
    
    def _build_resolve_section(self, parent):
        if self.current_role not in ("maintenance", "admin"):
            return

        resolve_frame = ttk.LabelFrame(
            parent,
            text="Resolve Request",
            padding=12
        )
        resolve_frame.pack(fill="x")

        ttk.Label(
            resolve_frame,
            text="Select a request first from 'Maintenance Req'."
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 10))

        ttk.Label(
            resolve_frame,
            text="Selected Request ID"
        ).grid(row=1, column=0, sticky="w", padx=6, pady=6)

        ttk.Label(
            resolve_frame,
            textvariable=self.selected_id_var
        ).grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(
            resolve_frame,
            text="Resolution Note"
        ).grid(row=2, column=0, sticky="nw", padx=6, pady=6)

        self.resolution_text = tk.Text(resolve_frame, width=40, height=6)
        self.resolution_text.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(
            resolve_frame,
            text="Hours Spent"
        ).grid(row=3, column=0, sticky="w", padx=6, pady=6)

        ttk.Entry(
            resolve_frame,
            textvariable=self.hours_spent_var,
            width=18
        ).grid(row=3, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(
            resolve_frame,
            text="Cost"
        ).grid(row=4, column=0, sticky="w", padx=6, pady=6)

        ttk.Entry(
            resolve_frame,
            textvariable=self.cost_var,
            width=18
        ).grid(row=4, column=1, sticky="w", padx=6, pady=6)

        ttk.Button(
            resolve_frame,
            text="Mark as Resolved",
            command=self.resolve_selected_request
        ).grid(row=5, column=1, sticky="w", padx=6, pady=(10, 0))


    def create_request(self):
        try:
            apartment_id_text = self.create_apartment_id_var.get().strip()
            selected_label = self.create_tenant_var.get().strip()
            title = self.create_title_var.get().strip()
            description = self.create_description_text.get("1.0", tk.END).strip()
            priority = self.create_priority_combo.get().strip()

            apartment_id = int(apartment_id_text) if apartment_id_text else None

            tenant_id = None
            for item in self.tenant_options:
                if item["label"] == selected_label:
                    tenant_id = item["tenantID"]
                    break

            if tenant_id is None:
                messagebox.showwarning("Missing Tenant", "Please select a tenant.")
                return

            if not title:
                messagebox.showwarning("Missing Title", "Please enter a request title.")
                return

            self.dao.add_request(
                apartmentID=apartment_id,
                tenantID=tenant_id,
                title=title,
                description=description,
                priority=priority,
                status="Open"
            )

            messagebox.showinfo("Created", "Maintenance request created successfully.")

            self.create_apartment_id_var.set("")
            self.create_tenant_var.set("")
            self.create_title_var.set("")
            self.create_description_text.delete("1.0", tk.END)
            self.create_priority_combo.set("Medium")

            # Move to request list and refresh it
            self.show_section("requests")

        except ValueError:
            messagebox.showwarning("Invalid Input", "Apartment ID must be numeric if present.")
               
    def load_data(self):
        if self.tree is None or not self.tree.winfo_exists():
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.dao.get_all_requests():
            self.tree.insert(
                "",
                tk.END,
                values=(
                    row.get("requestID", ""),
                    row.get("title", ""),
                    row.get("priority", ""),
                    row.get("status", ""),
                    row.get("assigned_staff", "") or "-",
                    row.get("scheduled_date", "") or "-",
                    row.get("scheduled_time", "") or "-",
                    f"{float(row.get('cost', 0) or 0):.2f}",
                    float(row.get("hours_spent", 0) or 0),
                ),
            )

        self.selected_request_id = None
        self.selected_id_var.set("None")

    def on_select_request(self, _event=None):
        # Read the selected table row and copy its data into the form fields.
        selected = self.tree.selection()
        if not selected:
            self.selected_request_id = None
            self.selected_id_var.set("None")
            return

        values = self.tree.item(selected[0], "values")
        self.selected_request_id = values[0]
        self.selected_id_var.set(str(values[0]))

        self.assigned_staff_var.set("" if values[4] == "-" else values[4])
        self.scheduled_date_var.set("" if values[5] == "-" else values[5])
        self.scheduled_time_var.set("" if values[6] == "-" else values[6])
        self.schedule_priority_var.set(values[2] or "Medium")
        if self.priority_combo is not None and self.priority_combo.winfo_exists():
            self.priority_combo.set(values[2] or "Medium")
        self.hours_spent_var.set(str(values[8]))
        self.cost_var.set(str(values[7]))

    def schedule_selected_request(self):
        # Schedule or update the selected maintenance request.
        if not self.selected_request_id:
            messagebox.showwarning("No Selection", "Please select a maintenance request first.")
            return

        assigned_staff = self.assigned_staff_var.get().strip()
        scheduled_date = self.scheduled_date_var.get().strip()
        scheduled_time = self.scheduled_time_var.get().strip()
        priority = self.schedule_priority_var.get().strip()

        if not assigned_staff or not scheduled_date or not scheduled_time:
            messagebox.showwarning(
                "Missing Details",
                "Please enter assigned staff, scheduled date, and scheduled time."
            )
            return

        self.dao.schedule_request(
            self.selected_request_id,
            assigned_staff,
            scheduled_date,
            scheduled_time,
            priority
        )
        messagebox.showinfo("Updated", "Request scheduled successfully.")
        self.load_data()

    def resolve_selected_request(self):
        # Mark the selected request as resolved and save time/cost details.
        if not self.selected_request_id:
            messagebox.showwarning("No Selection", "Please select a maintenance request first.")
            return

        resolution_note = self.resolution_text.get("1.0", tk.END).strip()

        try:
            hours_spent = float(self.hours_spent_var.get().strip() or 0)
            cost = float(self.cost_var.get().strip() or 0)
        except ValueError:
            messagebox.showwarning("Invalid Input", "Hours and cost must be numeric.")
            return

        self.dao.resolve_request(
            self.selected_request_id,
            resolution_note,
            hours_spent,
            cost
        )
        messagebox.showinfo("Resolved", "Request marked as resolved.")
        self.resolution_text.delete("1.0", tk.END)
        self.load_data()

    def show_report(self):
        # Show a simple maintenance cost summary report.
        total, hours, count = self.dao.get_cost_report_data()
        report = (
            f"Resolved Tasks: {count}\n"
            f"Total Cost: £{total:.2f}\n"
            f"Total Labour: {hours:.1f} hrs"
        )
        messagebox.showinfo("Maintenance Cost Report", report)
    
    def auto_fill_apartment_from_tenant(self, _event=None):
        selected_label = self.create_tenant_var.get().strip()

        if not selected_label:
            self.create_apartment_id_var.set("")
            return

        tenant_id = None
        for item in self.tenant_options:
            if item["label"] == selected_label:
                tenant_id = item["tenantID"]
                break

        if tenant_id is None:
            self.create_apartment_id_var.set("")
            return

        apartment_id = self.dao.get_current_apartment_by_tenant(tenant_id)
        self.create_apartment_id_var.set("" if apartment_id is None else str(apartment_id))
    
    
class MaintenanceView(MaintenanceDashboardView):
    # Backward-compatible alias if older imports still use MaintenanceView.
    pass


if __name__ == "__main__":
    root = tk.Tk()
    app = MaintenanceDashboardView(root)
    root.mainloop()
