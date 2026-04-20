import os
from datetime import date, datetime
import tkinter as tk

import customtkinter as ctk

# Keep matplotlib cache writable in restricted environments.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from controllers.auth_controller import AuthController
from controllers.lease_controller import LeaseController
from controllers.maintenance_controller import MaintenanceController
from controllers.payment_controller import PaymentController
from dao.apartment_dao import ApartmentDAO
from dao.tenant_dao import TenantDAO
from views.premium_shell import PremiumAppShell


class DashboardView(tk.Frame):
    def __init__(
        self,
        parent,
        on_logout,
        open_user_management,
        open_tenant_management,
        open_apartment_management,
        open_lease_management,
    ):
        super().__init__(parent, bg="#FAF7F2")
        self.pack(fill="both", expand=True)

        self.current_user = AuthController.current_user
        self.role = self._row_value(self.current_user, "role_name", "")
        self.full_name = self._row_value(self.current_user, "full_name", "User")
        self.location = self._row_value(self.current_user, "location", "All Cities")
        self.occupancy_filter = "All Cities"
        self.open_lease_management = open_lease_management

        self._load_dashboard_data()

        nav_sections = [
            {"title": "Overview", "items": [
                {"label": "Dashboard", "action": lambda: None, "icon": "dashboard"}
            ]},
            {"title": "Management", "items": []},
            {
                "title": "Finance",
                "items": [
                    {"label": "Payments", "action": lambda: None, "icon": "payments"},
                    {"label": "Reports", "action": lambda: None, "icon": "reports"},
                ],
            },
            {"title": "Admin", "items": []},
        ]

        if AuthController.can_access_feature("tenant_management", self.role):
            nav_sections[1]["items"].append({"label": "Tenants", "action": open_tenant_management, "icon": "tenants"})

        if AuthController.can_access_feature("apartment_management", self.role):
            nav_sections[1]["items"].append({"label": "Apartments", "action": open_apartment_management, "icon": "apartments"})

        if AuthController.can_access_feature("lease_management", self.role):
            nav_sections[1]["items"].append({"label": "Leases", "action": open_lease_management, "icon": "leases"})
        # Keep User Access visible in sidebar for consistent navigation; guard logic still controls access.
        nav_sections[3]["items"].append({
            "label": "User Access",
            "action": open_user_management,
            "icon": "shield"
        })

        self.shell = PremiumAppShell(
            self,
            page_title="Dashboard",
            on_logout=on_logout,
            active_nav="Dashboard",
            nav_sections=nav_sections,
            search_placeholder="Search tenants, units...",
            location_label=self.location,
            on_search_change=self._filter_lease_table,
            on_search_submit=self._filter_lease_table,
            on_bell_click=self._show_alerts,
            on_settings_click=self._show_settings,
            notification_count=self.attention_count,
        )

        content = self.shell.content
        self._build_banner(content, open_tenant_management)
        self._build_stats(content)
        self._build_main_panels(content)

    @staticmethod
    def _row_value(row, key, default=""):
        try:
            return row[key]
        except Exception:
            return default

    def _load_local_icon(self, icon_name, size=(20, 20)):
        try:
            from PIL import Image, ImageTk
        except ImportError:
            return None

        possible_paths = [
            os.path.join("images", "icons", f"{icon_name}.png"),
            os.path.join("images", "icons", f"{icon_name}.jpg"),
            os.path.join("images", "icons", f"{icon_name}.jpeg"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    image = Image.open(path).convert("RGBA")
                    image = image.resize(size, Image.LANCZOS)
                    return ImageTk.PhotoImage(image)
                except Exception:
                    return None
        return None

    @staticmethod
    def _is_expiring_soon(end_date_text):
        try:
            end_date = datetime.strptime(str(end_date_text), "%Y-%m-%d").date()
            return 0 <= (end_date - date.today()).days <= 30
        except Exception:
            return False
        
    

    def _load_dashboard_data(self):
        self.apartments = ApartmentDAO.get_all_apartments()
        self.tenants = TenantDAO.get_all_tenants()
        self.leases = LeaseController.get_all_leases()
        self.requests = MaintenanceController.get_all_requests()
        self.payments = PaymentController.get_all_payments()

        self.open_requests = [r for r in self.requests if self._row_value(r, "status", "") != "Resolved"]
        self.high_priority_requests = [
            r for r in self.open_requests if self._row_value(r, "priority", "") in {"High", "Urgent"}
        ]
        self.overdue_payments = [p for p in self.payments if self._row_value(p, "status", "") == "Overdue"]
        self.expiring_leases = [l for l in self.leases if self._is_expiring_soon(self._row_value(l, "end_date", ""))]

        self.attention_count = len(self.high_priority_requests) + len(self.overdue_payments) + len(self.expiring_leases)
        self.filtered_leases = list(self.leases)

        city_totals = {}
        for apt in self.apartments:
            city = str(self._row_value(apt, "city", "Unknown")).strip()
            if city:
                city_totals[city] = city_totals.get(city, 0) + 1
        self.occupancy_options = ["All Cities"] + sorted(city_totals.keys())

    def _build_banner(self, parent, open_tenant_management):
        banner = ctk.CTkFrame(
            parent,
            fg_color="#1F1A12",
            corner_radius=18,
            border_width=1,
            border_color="#312817",
            height=110
        )
        banner.pack(fill="x", pady=(0, 14))
        banner.pack_propagate(False)

        left = ctk.CTkFrame(banner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(24, 12), pady=18)

        hello_name = self.full_name.split()[0] if self.full_name else "User"

        ctk.CTkLabel(
            left,
            text=f"Good morning, {hello_name} ✦",
            text_color="#D4AF4D",
            font=("Georgia", 22, "bold"),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            left,
            text=f"{self.attention_count} items need your attention today",
            text_color="#D8C7A8",
            font=("Arial", 15),
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

        ctk.CTkButton(
            banner,
            text="+  Register Tenant",
            command=open_tenant_management,
            fg_color="#D4AF4D",
            hover_color="#C29D3D",
            text_color="#241D12",
            corner_radius=14,
            font=("Arial", 14, "bold"),
            height=48,
            width=180,
        ).pack(side="right", padx=20, pady=20)

    def _build_stats(self, parent):
        stats_wrap = ctk.CTkFrame(parent, fg_color="#FAF7F2", corner_radius=0)
        stats_wrap.pack(fill="x", pady=(0, 14))
        for col in range(4):
            stats_wrap.grid_columnconfigure(col, weight=1)

        paid_total = sum(
            float(self._row_value(p, "amount", 0) or 0)
            for p in self.payments
            if self._row_value(p, "status", "") == "Paid"
        )
        occupied = len([a for a in self.apartments if self._row_value(a, "status", "") == "Occupied"])

        stats = [
            {"label": "TOTAL UNITS", "value": str(len(self.apartments)), "sub": f"{occupied} occupied", "icon": "totalunits"},
            {"label": "ACTIVE TENANTS", "value": str(len(self.tenants)), "sub": f"{len(self.expiring_leases)} expiring soon", "icon": "activetenants"},
            {"label": "RENT COLLECTED", "value": f"£{paid_total:,.0f}", "sub": f"{len(self.overdue_payments)} overdue payments", "icon": "rentcollected"},
            {"label": "OPEN ISSUES", "value": str(len(self.open_requests)), "sub": f"{len(self.high_priority_requests)} high priority", "icon": "openissues"},
        ]

        for idx, item in enumerate(stats):
            card = ctk.CTkFrame(
                stats_wrap,
                fg_color="#FFFFFF",
                corner_radius=18,
                border_width=1,
                border_color="#E8DED0",
                height=138,
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=5)
            card.grid_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="#FFFFFF", corner_radius=0)
            inner.pack(fill="both", expand=True, padx=16, pady=16)

            top = ctk.CTkFrame(inner, fg_color="#FFFFFF", corner_radius=0)
            top.pack(fill="x")

            icon_box = ctk.CTkFrame(
                top,
                fg_color="#F1E6D3",
                corner_radius=12,
                width=48,
                height=48
            )
            icon_box.pack(side="left")
            icon_box.pack_propagate(False)

            stat_icon = self._load_local_icon(item["icon"], size=(24, 24))
            if stat_icon:
                icon_label = tk.Label(icon_box, image=stat_icon, bg="#F1E6D3", bd=0, highlightthickness=0)
                icon_label.image = stat_icon
                icon_label.pack(expand=True)
            else:
                ctk.CTkLabel(
                    icon_box,
                    text="•",
                    text_color="#8A6420",
                    font=("Arial", 22, "bold"),
                ).pack(expand=True)

            text_wrap = ctk.CTkFrame(top, fg_color="#FFFFFF", corner_radius=0)
            text_wrap.pack(side="left", fill="both", expand=True, padx=(14, 0))

            ctk.CTkLabel(
                text_wrap,
                text=item["label"],
                text_color="#A19078",
                font=("Arial", 12, "bold"),
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                text_wrap,
                text=item["value"],
                text_color="#241D12",
                font=("Georgia", 24, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(6, 0))

            ctk.CTkLabel(
                text_wrap,
                text=item["sub"],
                text_color="#6E604A",
                font=("Arial", 13),
                anchor="w",
            ).pack(fill="x", pady=(8, 0))


    def _build_main_panels(self, parent):
        main = ctk.CTkFrame(parent, fg_color="#FAF7F2", corner_radius=0)
        main.pack(fill="both", expand=True)

        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        lease_panel = ctk.CTkFrame(
            main,
            fg_color="#FFFFFF",
            corner_radius=20,
            border_width=0
        )
        lease_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        self._panel_header(
            lease_panel,
            "Recent Lease Activity",
            action_text="View all →",
            action_callback=self.open_lease_management,
        )
        self._build_lease_table(lease_panel)

        right_stack = ctk.CTkFrame(main, fg_color="#FAF7F2", corner_radius=0)
        right_stack.grid(row=0, column=1, sticky="nsew")
        right_stack.grid_rowconfigure(0, weight=1)
        right_stack.grid_rowconfigure(1, weight=1)
        right_stack.grid_columnconfigure(0, weight=1)

        occupancy_panel = ctk.CTkFrame(
            right_stack,
            fg_color="#FFFFFF",
            corner_radius=20,
            border_width=0
        )
        occupancy_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self._panel_header(occupancy_panel, "Occupancy by City", show_occupancy_menu=True)
        self._occupancy_parent = occupancy_panel
        self._build_occupancy(occupancy_panel)

        activity_panel = ctk.CTkFrame(
            right_stack,
            fg_color="#FFFFFF",
            corner_radius=20,
            border_width=0
        )
        activity_panel.grid(row=1, column=0, sticky="nsew")
        self._panel_header(activity_panel, "Recent Activity", action_text="View log")
        self._build_activity(activity_panel)

    def _panel_header(self, parent, title, action_text=None, action_callback=None, show_occupancy_menu=False):
        header = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0, height=44)
        header.pack(fill="x", padx=0, pady=(0, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=title,
            text_color="#2C2416",
            font=("Arial", 16, "bold"),
            anchor="w"
        ).pack(side="left", padx=16)

        if show_occupancy_menu:
            self.occupancy_menu = ctk.CTkOptionMenu(
                header,
                values=self.occupancy_options,
                command=self._on_occupancy_selected,
                fg_color="#F3EFE7",
                button_color="#E3D7C1",
                button_hover_color="#D9CCB4",
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color="#2C2416",
                text_color="#9A7A2E",
                corner_radius=12,
                width=92,
                height=30,
                font=("Arial", 11, "bold"),
                dropdown_font=("Arial", 11),
            )
            self.occupancy_menu.set(self.occupancy_filter)
            self.occupancy_menu.pack(side="right", padx=12, pady=8)

        elif action_text:
            action = ctk.CTkLabel(
                header,
                text=action_text,
                text_color="#9A7A2E",
                font=("Arial", 12, "bold"),
                cursor="pointinghand",
            )
            action.pack(side="right", padx=12, pady=8)
            if action_callback:
                action.bind("<Button-1>", lambda _e: action_callback())

        ctk.CTkFrame(
            parent,
            fg_color="#EFE4D0",
            corner_radius=0,
            height=1
        ).pack(fill="x", padx=16, pady=0)

    def _build_lease_table(self, parent):
        wrap = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=0)
        wrap.pack(fill="both", expand=True, padx=14, pady=10)
        wrap.grid_columnconfigure(0, weight=5)
        wrap.grid_columnconfigure(1, weight=2)
        wrap.grid_columnconfigure(2, weight=2)
        wrap.grid_columnconfigure(3, weight=2)

        headers = ["TENANT", "UNIT", "LEASE END", "STATUS"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(
                wrap,
                text=text,
                text_color="#9E8F77",
                font=("Arial", 13, "bold"),
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=8, pady=(0, 8))

        ctk.CTkFrame(wrap, fg_color="#EFE4D0", corner_radius=0, height=1).grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=(0, 4)
        )

        self.lease_rows_container = ctk.CTkFrame(wrap, fg_color="#FFFFFF", corner_radius=0)
        self.lease_rows_container.grid(row=2, column=0, columnspan=4, sticky="nsew")
        self._render_lease_rows()

    def _render_lease_rows(self):
        for widget in self.lease_rows_container.winfo_children():
            widget.destroy()

        if not self.filtered_leases:
            ctk.CTkLabel(
                self.lease_rows_container,
                text="No lease records yet.",
                text_color="#6B5D44",
                font=("Arial", 12),
                anchor="w",
            ).pack(fill="x", pady=12)
            return

        for lease in self.filtered_leases[:5]:
            tenant = self._row_value(lease, "tenant", "Unknown")
            unit = self._row_value(lease, "apartment", "-")
            lease_end = self._format_month_year(self._row_value(lease, "end_date", ""))
            status = self._row_value(lease, "status", "")
            NI_number = self._get_tenant_ni(lease)

            row = ctk.CTkFrame(self.lease_rows_container, fg_color="#FFFFFF", corner_radius=0, height=74)
            row.pack(fill="x", pady=(4, 0))
            row.pack_propagate(False)

            row.grid_columnconfigure(0, weight=5)
            row.grid_columnconfigure(1, weight=2)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)

            tenant_col = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=0)
            tenant_col.grid(row=0, column=0, sticky="w", padx=(8, 12), pady=8)

            ctk.CTkLabel(
                tenant_col,
                text=tenant,
                text_color="#2C2416",
                font=("Arial", 13, "bold"),
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                tenant_col,
                text=f"NI: {NI_number}",
                text_color="#9E8F77",
                font=("Arial", 11),
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

            ctk.CTkLabel(
                row,
                text=unit,
                text_color="#6B5D44",
                font=("Arial", 14, "bold"),
                anchor="w",
            ).grid(row=0, column=1, sticky="w", padx=8)

            ctk.CTkLabel(
                row,
                text=lease_end,
                text_color="#6B5D44",
                font=("Arial", 14, "bold"),
                anchor="w",
            ).grid(row=0, column=2, sticky="w", padx=8)

            pill_bg, pill_fg = self._status_colors(status)
            ctk.CTkLabel(
                row,
                text=status,
                text_color=pill_fg,
                fg_color=pill_bg,
                corner_radius=16,
                font=("Arial", 12, "bold"),
                width=86,
                height=30,
            ).grid(row=0, column=3, sticky="w", padx=8)

            ctk.CTkFrame(
                self.lease_rows_container,
                fg_color="#F1EADF",
                corner_radius=0,
                height=1
            ).pack(fill="x", pady=(4, 2))

    @staticmethod
    def _status_colors(status):
        status_lower = str(status).strip().lower()
        if status_lower == "active":
            return "#EAF3EA", "#2E6A2E"
        if status_lower in {"expiring", "pending"}:
            return "#F5EBCF", "#8A6A12"
        if status_lower in {"notice given", "overdue", "ended"}:
            return "#F2E2E2", "#8A2F2F"
        if status_lower in {"new"}:
            return "#E5EDF9", "#2B5E9B"
        return "#ECE6DC", "#6B5D44"

    def _format_month_year(self, date_text):
        try:
            return datetime.strptime(str(date_text), "%Y-%m-%d").strftime("%b %Y")
        except Exception:
            return str(date_text)

    def _get_tenant_ni(self, lease):
        possible_keys = ["NI_number", "NI", "national_insurance", "national_insurance_number"]
        for key in possible_keys:
            value = self._row_value(lease, key, "")
            if str(value).strip():
                return str(value).strip().upper()

        tenant_name = str(self._row_value(lease, "tenant", "")).strip().lower()
        tenant_id = str(self._row_value(lease, "tenantID", "")).strip()

        for tenant in self.tenants:
            db_name = str(
                self._row_value(
                    tenant,
                    "name",
                    self._row_value(tenant, "full_name", "")
                )
            ).strip().lower()

            db_id = str(
                self._row_value(
                    tenant,
                    "tenantID",
                    self._row_value(tenant, "id", "")
                )
            ).strip()

            if tenant_id and db_id and tenant_id == db_id:
                return str(
                    self._row_value(
                        tenant,
                        "NI_number",
                        self._row_value(
                            tenant,
                            "NI",
                            self._row_value(tenant, "national_insurance_number", "N/A")
                        )
                    )
                ).strip().upper()

            if tenant_name and db_name and tenant_name == db_name:
                return str(
                    self._row_value(
                        tenant,
                        "NI_number",
                        self._row_value(
                            tenant,
                            "NI",
                            self._row_value(tenant, "national_insurance_number", "N/A")
                        )
                    )
                ).strip().upper()

        return "N/A"

    def _filter_lease_table(self, query):
        q = (query or "").strip().lower()
        if not q:
            self.filtered_leases = list(self.leases)
        else:
            self.filtered_leases = [
                lease
                for lease in self.leases
                if q in str(self._row_value(lease, "tenant", "")).lower()
                or q in str(self._row_value(lease, "apartment", "")).lower()
                or q in str(self._row_value(lease, "status", "")).lower()
                or q in str(self._row_value(lease, "end_date", "")).lower()
            ]
        self._render_lease_rows()

    def _on_occupancy_selected(self, selected_value):
        self.occupancy_filter = selected_value
        self._build_occupancy(self._occupancy_parent)

    def _build_occupancy(self, parent):
        if hasattr(self, "_occupancy_body") and self._occupancy_body.winfo_exists():
            self._occupancy_body.destroy()

        body = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=0)
        body.pack(fill="both", expand=True, padx=14, pady=12)
        self._occupancy_body = body

        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        city_totals = {}
        city_occupied = {}

        for apt in self.apartments:
            city = str(self._row_value(apt, "city", "Unknown")).strip()
            city_totals[city] = city_totals.get(city, 0) + 1
            if self._row_value(apt, "status", "") == "Occupied":
                city_occupied[city] = city_occupied.get(city, 0) + 1

        all_cities = sorted(city_totals.keys())

        if self.occupancy_filter == "All Cities":
            display_cities = all_cities[:5]
            total_units = len(self.apartments)
            occupied_units = sum(city_occupied.values())
        else:
            display_cities = [self.occupancy_filter]
            total_units = city_totals.get(self.occupancy_filter, 0)
            occupied_units = city_occupied.get(self.occupancy_filter, 0)

        overall_pct = int((occupied_units / total_units) * 100) if total_units else 0

        left = ctk.CTkFrame(body, fg_color="#FFFFFF", corner_radius=0)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 8))

        pie_fig = Figure(figsize=(2.2, 2.2), dpi=100, facecolor="#FFFFFF")
        pie_ax = pie_fig.add_subplot(111)
        pie_ax.pie(
            [overall_pct, max(0, 100 - overall_pct)],
            colors=["#C9A13B", "#EFE7DA"],
            startangle=90,
            counterclock=False,
            wedgeprops={"width": 0.16, "linewidth": 0},
        )
        pie_ax.text(0, 0, f"{overall_pct}%", ha="center", va="center",
                    color="#2C2416", fontsize=18, fontweight="bold")
        pie_ax.axis("equal")
        pie_ax.axis("off")
        pie_fig.tight_layout(pad=0.2)

        pie_chart = FigureCanvasTkAgg(pie_fig, master=left)
        pie_chart.draw()
        pie_chart.get_tk_widget().pack()

        self._occupancy_pie_chart = pie_chart

        ctk.CTkLabel(
            left,
            text="Overall Occupancy",
            text_color="#6E604A",
            font=("Arial", 13),
        ).pack(pady=(0, 4))

        right = ctk.CTkFrame(body, fg_color="#FFFFFF", corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        for city in display_cities:
            total = city_totals.get(city, 0)
            occupied = city_occupied.get(city, 0)
            pct = int((occupied / total) * 100) if total else 0

            row = ctk.CTkFrame(right, fg_color="#FFFFFF", corner_radius=0)
            row.pack(fill="x", pady=6)

            ctk.CTkLabel(
                row,
                text=city,
                text_color="#2C2416",
                font=("Arial", 12),
                width=92,
                anchor="w",
            ).pack(side="left")

            bar = tk.Canvas(row, width=150, height=10, bg="#FFFFFF", highlightthickness=0)
            bar.pack(side="left", padx=8)
            bar.create_rectangle(0, 2, 150, 8, fill="#EAE2D6", outline="#EAE2D6")
            bar.create_rectangle(0, 2, int(150 * pct / 100), 8, fill="#C9A13B", outline="#C9A13B")

            ctk.CTkLabel(
                row,
                text=f"{pct}%",
                text_color="#6B5D44",
                font=("Arial", 12, "bold"),
                width=40,
                anchor="e",
            ).pack(side="left")

    def _build_activity(self, parent):
        body = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=0)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        activity_rows = []
        for payment in self.payments[:4]:
            payment_date = self._row_value(payment, "payment_date", "")
            stamp = self._format_activity_date(payment_date)
            activity_rows.append(
                {
                    "title": f"Payment from tenant #{self._row_value(payment, 'tenantID', '-')}",
                    "subtitle": f"{self._row_value(payment, 'status', 'Unknown')} · £{float(self._row_value(payment, 'amount', 0) or 0):,.0f}",
                    "stamp": stamp,
                }
            )

        for request in self.requests[:4]:
            stamp = self._format_activity_date(self._row_value(request, "created_at", ""))
            activity_rows.append(
                {
                    "title": f"Maintenance: {self._row_value(request, 'title', 'Request')}",
                    "subtitle": f"{self._row_value(request, 'priority', '')} priority · {self._row_value(request, 'status', '')}",
                    "stamp": stamp,
                }
            )

        if not activity_rows:
            ctk.CTkLabel(body, text="No recent activity yet.", text_color="#6B5D44", font=("Arial", 12)).pack(anchor="w", pady=8)
            return

        for item in activity_rows[:6]:
            row = ctk.CTkFrame(body, fg_color="#FFFFFF", corner_radius=0)
            row.pack(fill="x", pady=(0, 6))

            left = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=0)
            left.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(left, text=item["title"], text_color="#2C2416", font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(left, text=item["subtitle"], text_color="#8D7E66", font=("Arial", 11), anchor="w").pack(fill="x")

            ctk.CTkLabel(row, text=item["stamp"], text_color="#A49378", font=("Arial", 11), anchor="e").pack(side="right", padx=(8, 0))
            ctk.CTkFrame(body, fg_color="#F1EADF", corner_radius=0, height=1).pack(fill="x", pady=(2, 6))

    @staticmethod
    def _format_activity_date(raw_date):
        try:
            parsed = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
            return parsed.strftime("%d %b %Y")
        except Exception:
            return "Today"

    def _show_alerts(self):
        self.shell.show_premium_info_modal(
            title="Alerts",
            icon_text="🔔",
            icon_fg="#B8891F",
            icon_bg="#F6E8B8",
            rows=[
                ("High-priority maintenance", len(self.high_priority_requests)),
                ("Overdue payments", len(self.overdue_payments)),
                ("Leases expiring in 30 days", len(self.expiring_leases)),
            ],
        )

    def _show_settings(self):
        role_text = str(self.role).replace("_", " ").title()

        self.shell.show_premium_info_modal(
            title="Account Settings",
            icon_bg="#F6EED7",
            rows=[
                ("User", self.full_name),
                ("Role", role_text),
                ("Location", self.location),
                ("Date", datetime.now().strftime("%d %b %Y")),
            ],
            icon_image_name="settings",
            icon_image_size=(34, 34),
        )
