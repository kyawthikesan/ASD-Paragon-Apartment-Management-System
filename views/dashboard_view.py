# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

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
from dao.location_dao import LocationDAO
from dao.tenant_dao import TenantDAO
from dao.report_dao import ReportDAO
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
        open_finance_dashboard,
        open_finance_payments=None,
        open_finance_reports=None,
    ):
        super().__init__(parent, bg="#FAF7F2")
        self.pack(fill="both", expand=True)

        # Store the logged-in user's basic details so the dashboard can
        # personalise content and limit data where needed.
        self.current_user = AuthController.current_user
        self.role = self._row_value(self.current_user, "role_name", "")
        self.full_name = self._row_value(self.current_user, "full_name", "User")
        self.location = self._row_value(self.current_user, "location", "All Cities")
        self.is_admin = AuthController.is_admin(self.role)

        # Admins can switch between cities; other roles stay limited to
        # their assigned location.
        self.occupancy_filter = "All Cities" if self.is_admin else (self.location or "All Cities")
        self.city_scope = AuthController.get_city_scope(self.occupancy_filter)

        # Save navigation callbacks used by buttons and panel actions.
        self.open_lease_management = open_lease_management
        self._open_tenant_management_callback = open_tenant_management
        self.open_finance_dashboard = open_finance_dashboard
        self.open_finance_payments = open_finance_payments or open_finance_dashboard
        self.open_finance_reports = open_finance_reports or open_finance_dashboard

        # Search state used to keep the lease table in sync with the search box.
        self._search_watch_job = None
        self._last_search_value = ""

        # Load all dashboard data before building the UI.
        self._load_dashboard_data()

        nav_sections = [
            {
                "title": "Overview",
                "items": [
                    {"label": "Dashboard", "action": lambda: None, "icon": "dashboard"}
                ],
            },
            {"title": "Management", "items": []},
            {"title": "Finance", "items": []},
            {"title": "Admin", "items": []},
        ]

        # Only show navigation items the current role is allowed to access.
        if AuthController.can_access_feature("tenant_management", self.role):
            nav_sections[1]["items"].append(
                {"label": "Tenants", "action": open_tenant_management, "icon": "tenants"}
            )

        if AuthController.can_access_feature("apartment_management", self.role):
            nav_sections[1]["items"].append(
                {"label": "Apartments", "action": open_apartment_management, "icon": "apartments"}
            )

        if AuthController.can_access_feature("lease_management", self.role):
            nav_sections[1]["items"].append(
                {"label": "Leases", "action": open_lease_management, "icon": "leases"}
            )

        if AuthController.can_access_feature("finance_dashboard", self.role):
            nav_sections[2]["items"].append(
                {
                    "label": "Payments",
                    "action": self.open_finance_payments,
                    "icon": "payments",
                }
            )
            nav_sections[2]["items"].append(
                {
                    "label": "Reports",
                    "action": self.open_finance_reports,
                    "icon": "reports",
                }
            )

        # Keep User Access visible for consistent sidebar layout.
        nav_sections[3]["items"].append(
            {
                "label": "User Access",
                "action": open_user_management,
                "icon": "shield",
            }
        )

        # Build the shared dashboard shell used across the system.
        self.shell = PremiumAppShell(
            self,
            page_title="Dashboard",
            on_logout=on_logout,
            active_nav="Dashboard",
            nav_sections=nav_sections,
            search_placeholder="Search tenants, apartments, leases...",
            location_label=self.location,
            on_search_change=self._filter_lease_table,
            on_search_submit=self._filter_lease_table,
            on_bell_click=self._show_alerts,
            on_settings_click=self._show_settings,
            notification_count=self.attention_count,
        )
        self.shell.pack(fill="both", expand=True)

        self.content = self.shell.content
        self._bind_search_handlers()
        self._render_dashboard_content(open_tenant_management)

    def _render_dashboard_content(self, open_tenant_management):
        # Clear and rebuild the main dashboard area whenever data or filters change.
        for widget in self.content.winfo_children():
            widget.destroy()
        self._build_banner(self.content, open_tenant_management)
        self._build_stats(self.content)
        self._build_main_panels(self.content)

    @staticmethod
    def _row_value(row, key, default=""):
        # Safely read values from database rows without crashing if a key is missing.
        try:
            return row[key]
        except Exception:
            return default

    def _load_local_icon(self, icon_name, size=(20, 20)):
        # Try to load a local icon image for stat cards and other UI elements.
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
        # A lease is treated as expiring soon if it ends within the next 30 days.
        try:
            end_date = datetime.strptime(str(end_date_text), "%Y-%m-%d").date()
            return 0 <= (end_date - date.today()).days <= 30
        except Exception:
            return False

    def _load_dashboard_data(self):
        # Refresh all dashboard datasets based on the current city filter.
        self.city_scope = AuthController.get_city_scope(self.occupancy_filter)
        self.apartments = ApartmentDAO.get_all_apartments(city=self.city_scope)
        self.tenants = TenantDAO.get_all_tenants()
        self.leases = LeaseController.get_all_leases(city=self.city_scope)
        self.requests = MaintenanceController.get_all_requests(city=self.city_scope)
        self.payments = PaymentController.get_all_payments(city=self.city_scope)

        # Separate unresolved requests so open issues can be counted easily.
        self.open_requests = [
            r for r in self.requests
            if str(self._row_value(r, "status", "")).strip().lower() != "resolved"
        ]

        # Highlight requests that need more urgent attention.
        self.high_priority_requests = [
            r for r in self.open_requests
            if str(self._row_value(r, "priority", "")).strip().lower() in {"high", "urgent"}
        ]

        # Use the report layer for overdue payment data so finance totals stay accurate.
        self.overdue_payments = ReportDAO.get_late_invoices(city=self.city_scope)

        self.expiring_leases = [
            l for l in self.leases
            if self._is_expiring_soon(self._row_value(l, "end_date", ""))
        ]

        # Total notification count shown in the dashboard header.
        self.attention_count = (
            len(self.high_priority_requests)
            + len(self.overdue_payments)
            + len(self.expiring_leases)
        )

        # By default, the lease table shows every lease until a search is applied.
        self.filtered_leases = list(self.leases)

        city_totals = {}
        for apt in self.apartments:
            city = str(self._row_value(apt, "city", "Unknown")).strip()
            if city:
                city_totals[city] = city_totals.get(city, 0) + 1

        # Admins can view all cities in the occupancy menu.
        if self.is_admin:
            locations = LocationDAO.get_all_locations()
            cities = sorted({str(loc["city"]).strip() for loc in locations if str(loc["city"]).strip()})
            self.occupancy_options = ["All Cities"] + cities
            if self.occupancy_filter not in self.occupancy_options:
                self.occupancy_filter = "All Cities"
        else:
            # Non-admin users only get their own location or the available city list.
            self.occupancy_options = [self.location] if self.location else sorted(city_totals.keys())
            if self.occupancy_options:
                self.occupancy_filter = self.occupancy_options[0]

    def _build_banner(self, parent, open_tenant_management):
        # Top banner showing greeting and a quick action button.
        banner = ctk.CTkFrame(
            parent,
            fg_color="#1F1A12",
            corner_radius=18,
            border_width=1,
            border_color="#312817",
            height=110,
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
        # Summary cards across the top of the dashboard.
        stats_wrap = ctk.CTkFrame(parent, fg_color="#FAF7F2", corner_radius=0)
        stats_wrap.pack(fill="x", pady=(0, 14))
        for col in range(4):
            stats_wrap.grid_columnconfigure(col, weight=1)

        summary = ReportDAO.get_overall_financial_summary(city=self.city_scope)
        paid_total = float(summary["total_collected"] or 0)

        occupied = len([
            a for a in self.apartments
            if str(self._row_value(a, "status", "")).strip().lower() == "occupied"
        ])

        stats = [
            {
                "label": "TOTAL UNITS",
                "value": str(len(self.apartments)),
                "sub": f"{occupied} occupied",
                "icon": "totalunits",
            },
            {
                "label": "ACTIVE TENANTS",
                "value": str(len(self.tenants)),
                "sub": f"{len(self.expiring_leases)} expiring soon",
                "icon": "activetenants",
            },
            {
                "label": "RENT COLLECTED",
                "value": f"£{paid_total:,.0f}",
                "sub": f"{len(self.overdue_payments)} overdue payments",
                "icon": "rentcollected",
            },
            {
                "label": "OPEN ISSUES",
                "value": str(len(self.open_requests)),
                "sub": f"{len(self.high_priority_requests)} high priority",
                "icon": "openissues",
            },
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
                height=48,
            )
            icon_box.pack(side="left")
            icon_box.pack_propagate(False)

            stat_icon = self._load_local_icon(item["icon"], size=(24, 24))
            if stat_icon:
                icon_label = tk.Label(
                    icon_box,
                    image=stat_icon,
                    bg="#F1E6D3",
                    bd=0,
                    highlightthickness=0,
                )
                icon_label.image = stat_icon
                icon_label.pack(expand=True)
            else:
                # Fallback dot if the icon file is missing.
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
        # Main lower section: lease table on the left, charts/activity on the right.
        main = ctk.CTkFrame(parent, fg_color="#FAF7F2", corner_radius=0)
        main.pack(fill="both", expand=True)

        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        lease_panel = ctk.CTkFrame(
            main,
            fg_color="#FFFFFF",
            corner_radius=20,
            border_width=0,
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
            border_width=0,
        )
        occupancy_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self._panel_header(occupancy_panel, "Occupancy by City", show_occupancy_menu=True)
        self._occupancy_parent = occupancy_panel
        self._build_occupancy(occupancy_panel)

        activity_panel = ctk.CTkFrame(
            right_stack,
            fg_color="#FFFFFF",
            corner_radius=20,
            border_width=0,
        )
        activity_panel.grid(row=1, column=0, sticky="nsew")
        self._panel_header(
            activity_panel,
            "Recent Activity",
            action_text="View log",
            action_callback=self._show_activity_log,
        )
        self._build_activity(activity_panel)

    def _panel_header(
        self,
        parent,
        title,
        action_text=None,
        action_callback=None,
        show_occupancy_menu=False,
    ):
        # Shared panel header so all dashboard panels stay visually consistent.
        header = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0, height=44)
        header.pack(fill="x", padx=0, pady=(0, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=title,
            text_color="#2C2416",
            font=("Arial", 16, "bold"),
            anchor="w",
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
            height=1,
        ).pack(fill="x", padx=16, pady=0)

    def _build_lease_table(self, parent):
        # Creates the lease table structure, then fills the rows separately.
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
        # Refresh only the lease rows so searching does not rebuild the full dashboard.
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
            tenant_id = self._get_tenant_id(lease)

            row = ctk.CTkFrame(
                self.lease_rows_container,
                fg_color="#FFFFFF",
                corner_radius=0,
                height=74,
            )
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
                text=f"ID: {tenant_id}",
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
                height=1,
            ).pack(fill="x", pady=(4, 2))

    @staticmethod
    def _status_colors(status):
        # Return badge colours based on lease/payment/request status.
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
        # Convert database date format into a shorter UI-friendly format.
        try:
            return datetime.strptime(str(date_text), "%Y-%m-%d").strftime("%b %Y")
        except Exception:
            return str(date_text)

    def _get_tenant_id(self, lease):
        # Try the most likely tenant ID fields first.
        possible_keys = ["tenantID", "tenant_id", "id"]
        for key in possible_keys:
            value = self._row_value(lease, key, "")
            if str(value).strip():
                return str(value).strip()

        # If no direct ID is stored on the lease row, match it back to the tenant list.
        tenant_name = str(self._row_value(lease, "tenant", "")).strip().lower()
        tenant_id = str(self._row_value(lease, "tenantID", "")).strip()

        for tenant in self.tenants:
            db_name = str(
                self._row_value(
                    tenant,
                    "name",
                    self._row_value(tenant, "full_name", ""),
                )
            ).strip().lower()

            db_id = str(
                self._row_value(
                    tenant,
                    "tenantID",
                    self._row_value(tenant, "id", ""),
                )
            ).strip()

            if tenant_id and db_id and tenant_id == db_id:
                return db_id

            if tenant_name and db_name and tenant_name == db_name:
                return db_id or "N/A"

        return "N/A"

    def _filter_lease_table(self, query):
        # Filter the visible lease list based on the current search input.
        self._last_search_value = (query or "").strip()
        q = self._last_search_value.casefold()
        try:
            if not q:
                self.filtered_leases = list(self.leases)
            else:
                self.filtered_leases = [
                    lease
                    for lease in self.leases
                    if self._lease_matches_query(lease, q)
                ]
        except Exception:
            # Keep UI responsive even if a malformed row is encountered.
            self.filtered_leases = list(self.leases)
        self._render_lease_rows()

    def _lease_matches_query(self, lease, query):
        # Normalise strings so searching works even with mixed cases or separators.
        def normalize(text):
            return " ".join(str(text or "").replace("_", " ").replace("-", " ").split()).casefold()

        tenant = normalize(self._row_value(lease, "tenant", ""))
        apartment = normalize(self._row_value(lease, "apartment", ""))
        status = normalize(self._row_value(lease, "status", ""))
        end_date = normalize(self._row_value(lease, "end_date", ""))
        tenant_id = normalize(self._get_tenant_id(lease))
        lease_id = normalize(self._row_value(lease, "leaseID", self._row_value(lease, "id", "")))

        # Keep backward-compatible matching for legacy datasets that may still
        # include NI identifiers, while no longer displaying them in the UI.
        legacy_ni = normalize(
            self._row_value(
                lease,
                "NI_number",
                self._row_value(
                    lease,
                    "NI",
                    self._row_value(lease, "national_insurance_number", ""),
                ),
            )
        )

        searchable = [tenant, apartment, status, end_date, tenant_id, lease_id, legacy_ni]
        if any(query in field for field in searchable):
            return True

        # Also allow partial word matching, useful when the user only types the start.
        tokens = []
        for field in searchable:
            tokens.extend(part for part in field.split() if part)
        return any(token.startswith(query) for token in tokens)

    def _bind_search_handlers(self):
        # Search events are already handled by PremiumAppShell callbacks.
        # Keeping extra bindings here causes duplicate filter calls and lag.
        return

    def _start_search_watch(self):
        # Start a lightweight polling loop in case text changes without a key event.
        if self._search_watch_job:
            try:
                self.after_cancel(self._search_watch_job)
            except Exception:
                pass
        self._search_watch_job = self.after(150, self._poll_search_entry)

    def _poll_search_entry(self):
        self._search_watch_job = None
        try:
            entry = getattr(self.shell, "search_entry", None)
            if not entry or not entry.winfo_exists():
                return
            current_value = (entry.get() or "").strip()
            if current_value != self._last_search_value:
                self._filter_lease_table(current_value)
        except Exception:
            return
        self._search_watch_job = self.after(150, self._poll_search_entry)

    def _on_occupancy_selected(self, selected_value):
        # Changing the city filter refreshes dashboard data for admins.
        self.occupancy_filter = selected_value
        if self.is_admin:
            self._load_dashboard_data()
            self._render_dashboard_content(self._open_tenant_management_callback)
        else:
            self._build_occupancy(self._occupancy_parent)

    def _build_occupancy(self, parent):
        # Rebuild only the occupancy section when the selected city changes.
        if hasattr(self, "_occupancy_body") and self._occupancy_body.winfo_exists():
            self._occupancy_body.destroy()

        parent.update_idletasks()
        panel_width = max(parent.winfo_width(), 320)
        panel_height = max(parent.winfo_height(), 220)
        compact_mode = panel_width < 560 or panel_height < 320

        body = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=0)
        body.pack(fill="both", expand=True, padx=14, pady=12)
        self._occupancy_body = body

        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=0)
        body.grid_columnconfigure(2, weight=1)

        city_totals = {}
        city_occupied = {}

        for apt in self.apartments:
            city = str(self._row_value(apt, "city", "Unknown")).strip()
            city_totals[city] = city_totals.get(city, 0) + 1

            if str(self._row_value(apt, "status", "")).strip().lower() == "occupied":
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
        left.grid(row=0, column=0, sticky="nw", padx=(0, 8), pady=0)

        # Keep the donut inside panel bounds on short screens.
        chart_px = int(max(120, min(220, panel_width * 0.34, panel_height - 92)))

        # Circular chart showing overall occupancy percentage.
        pie_size = chart_px / 100
        pie_fig = Figure(figsize=(pie_size, pie_size), dpi=100, facecolor="#FFFFFF")
        pie_ax = pie_fig.add_subplot(111)
        pie_ax.pie(
            [overall_pct, max(0, 100 - overall_pct)],
            colors=["#C9A13B", "#EFE7DA"],
            startangle=90,
            counterclock=False,
            wedgeprops={"width": 0.18 if compact_mode else 0.16, "linewidth": 0},
        )
        pie_ax.text(
            0,
            0,
            f"{overall_pct}%",
            ha="center",
            va="center",
            color="#2C2416",
            fontsize=14 if compact_mode else 18,
            fontweight="bold",
        )
        pie_ax.axis("equal")
        pie_ax.axis("off")
        # Reserve a little extra space so the ring edge is never clipped.
        pie_fig.subplots_adjust(left=0.03, right=0.97, top=0.97, bottom=0.10)

        pie_chart = FigureCanvasTkAgg(pie_fig, master=left)
        pie_chart.draw()
        pie_chart.get_tk_widget().pack(pady=(0, 2))

        self._occupancy_pie_chart = pie_chart

        ctk.CTkLabel(
            left,
            text="Overall Occupancy",
            text_color="#6E604A",
            font=("Arial", 11 if compact_mode else 13),
        ).pack(pady=(0, 2 if compact_mode else 4))

        gutter = max(14, min(24, int(panel_width * 0.025)))
        body.grid_columnconfigure(1, minsize=gutter)

        right = ctk.CTkFrame(body, fg_color="#FFFFFF", corner_radius=0)
        right.grid(row=0, column=2, sticky="nsew", padx=(0, 0), pady=0)
        right.update_idletasks()

        # Show a simple progress bar for each displayed city.
        city_label_width = 74 if compact_mode else 92
        pct_label_width = 34 if compact_mode else 40
        for city in display_cities:
            total = city_totals.get(city, 0)
            occupied = city_occupied.get(city, 0)
            pct = int((occupied / total) * 100) if total else 0

            row = ctk.CTkFrame(right, fg_color="#FFFFFF", corner_radius=0)
            row.pack(fill="x", pady=4 if compact_mode else 6)
            row.grid_columnconfigure(0, weight=0)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=0)

            ctk.CTkLabel(
                row,
                text=city,
                text_color="#2C2416",
                font=("Arial", 11 if compact_mode else 12),
                width=city_label_width,
                anchor="w",
            ).grid(row=0, column=0, sticky="w")

            bar = tk.Canvas(row, height=10, bg="#FFFFFF", highlightthickness=0)
            bar.grid(row=0, column=1, sticky="ew", padx=8)

            def _draw_bar(event, canvas=bar, value=pct):
                width = max(1, int(event.width))
                canvas.delete("all")
                canvas.create_rectangle(0, 2, width, 8, fill="#EAE2D6", outline="#EAE2D6")
                canvas.create_rectangle(0, 2, int(width * value / 100), 8, fill="#C9A13B", outline="#C9A13B")

            bar.bind("<Configure>", _draw_bar)

            ctk.CTkLabel(
                row,
                text=f"{pct}%",
                text_color="#6B5D44",
                font=("Arial", 11 if compact_mode else 12, "bold"),
                width=pct_label_width,
                anchor="e",
            ).grid(row=0, column=2, sticky="e")

    def _build_activity(self, parent):
        # Small activity preview shown on the dashboard.
        body = ctk.CTkScrollableFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=0,
            scrollbar_button_color="#D7C8AE",
            scrollbar_button_hover_color="#C8B28F",
        )
        body.pack(fill="both", expand=True, padx=12, pady=10)
        activity_rows = self._build_activity_feed(limit=6)

        if not activity_rows:
            ctk.CTkLabel(
                body,
                text="No recent activity yet.",
                text_color="#6B5D44",
                font=("Arial", 12),
            ).pack(anchor="w", pady=8)
            return

        for item in activity_rows[:6]:
            row = ctk.CTkFrame(body, fg_color="#FFFFFF", corner_radius=0)
            row.pack(fill="x", pady=(0, 6))

            left = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=0)
            left.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                left,
                text=item["title"],
                text_color="#2C2416",
                font=("Arial", 13, "bold"),
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                left,
                text=item["subtitle"],
                text_color="#8D7E66",
                font=("Arial", 11),
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                row,
                text=item["stamp"],
                text_color="#A49378",
                font=("Arial", 11),
                anchor="e",
            ).pack(side="right", padx=(8, 0))

            ctk.CTkFrame(
                body,
                fg_color="#F1EADF",
                corner_radius=0,
                height=1,
            ).pack(fill="x", pady=(2, 6))

    def _build_activity_feed(self, limit=None):
        # Combine payment and maintenance records into one timeline.
        activity_rows = []

        for payment in self.payments:
            raw_date = self._row_value(payment, "created_at", "") or self._row_value(
                payment, "payment_date", ""
            )
            parsed_date = self._parse_activity_datetime(raw_date)

            tenant_name = self._row_value(
                payment,
                "tenant_name",
                f"Tenant #{self._row_value(payment, 'tenantID', '-')}",
            )
            amount_paid = float(
                self._row_value(
                    payment,
                    "amount_paid",
                    self._row_value(payment, "amount", 0),
                ) or 0
            )
            payment_method = str(self._row_value(payment, "payment_method", "Manual")).strip()

            activity_rows.append(
                {
                    "title": f"Payment from {tenant_name}",
                    "subtitle": f"{payment_method} · £{amount_paid:,.0f}",
                    "stamp": self._format_activity_date(raw_date),
                    "category": "Payment",
                    "sort_value": parsed_date or datetime.min,
                }
            )

        for request in self.requests:
            raw_date = self._row_value(request, "created_at", "")
            parsed_date = self._parse_activity_datetime(raw_date)
            activity_rows.append(
                {
                    "title": f"Maintenance: {self._row_value(request, 'title', 'Request')}",
                    "subtitle": (
                        f"{self._row_value(request, 'priority', '')} priority · "
                        f"{self._row_value(request, 'status', '')}"
                    ),
                    "stamp": self._format_activity_date(raw_date),
                    "category": "Maintenance",
                    "sort_value": parsed_date or datetime.min,
                }
            )

        # Newest activity should appear first.
        activity_rows.sort(key=lambda item: item["sort_value"], reverse=True)
        for item in activity_rows:
            item.pop("sort_value", None)

        if limit is not None:
            return activity_rows[:limit]
        return activity_rows

    def _show_activity_log(self):
        # Open a larger pop-up window with the full activity history.
        dialog = ctk.CTkToplevel(self)
        dialog.title("Activity Log")
        self._center_dialog(dialog, 760, 560)
        dialog.grab_set()
        dialog.configure(fg_color="#F8F5F0")
        scope_text = "all cities" if self.is_admin else "your current city scope"

        body = ctk.CTkFrame(dialog, fg_color="#F8F5F0", corner_radius=0)
        body.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            body,
            text="Activity Log",
            text_color="#2C2416",
            font=("Georgia", 28, "bold"),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            body,
            text=f"Payments and maintenance events in {scope_text}.",
            text_color="#7A6A50",
            font=("Arial", 12),
            anchor="w",
        ).pack(fill="x", pady=(6, 12))

        content = ctk.CTkFrame(
            body,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color="#E3D9C9",
        )
        content.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(
            content,
            fg_color="#FFFFFF",
            corner_radius=0,
            scrollbar_button_color="#D9CCB4",
            scrollbar_button_hover_color="#CBB78E",
        )
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        entries = self._build_activity_feed()
        if not entries:
            ctk.CTkLabel(
                scroll,
                text="No activity records available.",
                text_color="#6B5D44",
                font=("Arial", 13),
                anchor="w",
            ).pack(fill="x", pady=8, padx=8)
        else:
            for item in entries:
                row = ctk.CTkFrame(scroll, fg_color="#FFFFFF", corner_radius=0)
                row.pack(fill="x", pady=(2, 6), padx=8)

                top = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=0)
                top.pack(fill="x")

                ctk.CTkLabel(
                    top,
                    text=item["title"],
                    text_color="#2C2416",
                    font=("Arial", 13, "bold"),
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    top,
                    text=item["stamp"],
                    text_color="#A49378",
                    font=("Arial", 11),
                    anchor="e",
                ).pack(side="right")

                ctk.CTkLabel(
                    row,
                    text=item["subtitle"],
                    text_color="#7D6F57",
                    font=("Arial", 11),
                    anchor="w",
                ).pack(fill="x", pady=(2, 0))

                ctk.CTkFrame(
                    scroll,
                    fg_color="#F1EADF",
                    corner_radius=0,
                    height=1,
                ).pack(fill="x", padx=8, pady=(0, 4))

        actions = ctk.CTkFrame(body, fg_color="#F8F5F0", corner_radius=0)
        actions.pack(fill="x", pady=(12, 0))

        ctk.CTkButton(
            actions,
            text="Close",
            command=dialog.destroy,
            fg_color="#EEE7D9",
            hover_color="#E2D8C6",
            text_color="#5E5137",
            corner_radius=12,
            width=110,
            height=38,
            font=("Arial", 13, "bold"),
        ).pack(side="right")

    def _center_dialog(self, dialog, width, height):
        # Position pop-up windows in the centre of the main application.
        dialog.update_idletasks()
        root = self.winfo_toplevel()
        root.update_idletasks()
        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        rw, rh = root.winfo_width(), root.winfo_height()
        x = rx + max(0, (rw - width) // 2)
        y = ry + max(0, (rh - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def _parse_activity_datetime(raw_date):
        # Accept a few common date formats from different database fields.
        raw_text = str(raw_date or "").strip()
        if not raw_text:
            return None
        candidate = raw_text.replace("Z", "+00:00")

        parsers = (
            datetime.fromisoformat,
            lambda value: datetime.strptime(value, "%Y-%m-%d"),
            lambda value: datetime.strptime(value, "%Y-%m-%d %H:%M:%S"),
        )
        for parser in parsers:
            try:
                return parser(candidate)
            except Exception:
                continue
        return None

    @staticmethod
    def _format_activity_date(raw_date):
        # Show a fallback label if no valid date is available.
        parsed = DashboardView._parse_activity_datetime(raw_date)
        if not parsed:
            return "Today"
        return parsed.date().strftime("%d %b %Y")

    def _show_alerts(self):
        # Quick summary of issues that need attention.
        self.shell.show_premium_info_modal(
            title="Alerts",
            icon_text="🔔",
            icon_fg="#B8891F",
            icon_bg="#F6E8B8",
            highlight_nonzero=True,
            rows=[
                ("High-priority maintenance", str(len(self.high_priority_requests))),
                ("Overdue payments", str(len(self.overdue_payments))),
                ("Leases expiring in 30 days", str(len(self.expiring_leases))),
            ],
        )

    def _show_settings(self):
        # Display account details relevant to the logged-in user.
        role_text = str(self.role).replace("_", " ").title()
        is_admin = str(self.role).strip().lower() == "admin"
        rows = [
            ("User", self.full_name),
            ("Role", role_text),
        ]
        if is_admin:
            rows.append(("Location Access", "Full location access (All Cities)"))
        else:
            rows.insert(2, ("Location", self.location))

        self.shell.show_premium_info_modal(
            title="Account Settings",
            icon_bg="#F6EED7",
            rows=rows,
            icon_image_name="settings",
            icon_image_size=(34, 34),
        )
