# Student Name: Kyaw Thike (oliver) San
# Student ID: 25014001
# Module: UFCF8S-30-2 Advanced Software Development

# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import date, datetime, timedelta
import customtkinter as ctk
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except Exception:
    FigureCanvasTkAgg = None
    Figure = None
    MATPLOTLIB_AVAILABLE = False

from dao.lease_dao import LeaseDAO
from dao.invoice_dao import InvoiceDAO
from dao.payment_dao import PaymentDAO
from dao.report_dao import ReportDAO
from dao.location_dao import LocationDAO
from dao.maintenance_dao import MaintenanceDAO
from controllers.auth_controller import AuthController
from views.premium_shell import PremiumAppShell


class FinanceDashboardView(ttk.Frame):
    def __init__(
        self,
        parent,
        logout_callback=None,
        home_callback=None,
        initial_tab="Invoices",
        visible_tabs=None,
        open_tenant_management=None,
        open_apartment_management=None,
        open_lease_management=None,
        open_finance_payments=None,
        open_finance_reports=None,
        open_user_management=None,
        open_maintenance_dashboard=None,
    ):
        super().__init__(parent)
        self.parent = parent
        self.logout_callback = logout_callback
        self.home_callback = home_callback
        self.open_tenant_management = open_tenant_management or home_callback
        self.open_apartment_management = open_apartment_management or home_callback
        self.open_lease_management = open_lease_management or home_callback
        self.open_finance_payments = open_finance_payments
        self.open_finance_reports = open_finance_reports
        self.open_user_management = open_user_management or home_callback
        self.open_maintenance_dashboard = open_maintenance_dashboard or home_callback
        self.initial_tab = initial_tab
        self.role = str(AuthController.get_current_role() or "").strip().lower()
        self.is_admin = AuthController.is_admin()
        self.selected_city = "All Cities" if self.is_admin else (AuthController.get_current_location() or "All Cities")
        self.city_scope = AuthController.get_city_scope(self.selected_city)

        self.pack(fill="both", expand=True)

        self.lease_map = {}
        self.invoice_map = {}
        self._all_tabs = ("Invoices", "Payments", "Reports")
        requested_tabs = tuple(visible_tabs) if visible_tabs else self._all_tabs
        self.enabled_tabs = tuple(tab for tab in self._all_tabs if tab in requested_tabs) or self._all_tabs
        self._search_query = ""

        self._build_layout()
        self._select_initial_tab()
        self.refresh_all()

    # =========================
    # MAIN LAYOUT
    # =========================
    def _build_layout(self):
        content_parent = self
        self.finance_banner_tabs = None
        if self.role in {"admin", "manager", "finance"}:
            active_nav = "Reports" if str(self.initial_tab).strip().lower() == "reports" else "Payments"
            hide_sidebar = self.role == "finance"
            self.shell = PremiumAppShell(
                self,
                page_title="Payments & Reports",
                on_logout=(self.logout_callback or self.home_callback) if hide_sidebar else (self.home_callback or self.logout_callback),
                active_nav=active_nav,
                nav_sections=self._build_nav_sections(),
                footer_action_label="Logout" if hide_sidebar else ("Back to Dashboard" if self.home_callback else "Logout"),
                search_placeholder="Search invoices and receipts...",
                location_label=AuthController.get_current_location(),
                on_search_change=self._on_shell_search,
                on_search_submit=self._on_shell_search,
                on_bell_click=self._show_alerts,
                on_settings_click=self._show_settings,
                hide_sidebar=hide_sidebar,
            )
            content_parent = self.shell.content

        layout_parent = self if content_parent is self else content_parent
        if self.role == "finance" and hasattr(self, "shell"):
            self._build_finance_identity_banner(layout_parent)

        self.tab_switch_buttons = {}
        show_switches = len(self.enabled_tabs) > 1
        self._show_switches = show_switches
        self._compact_controls = None
        compact_controls = None
        if (show_switches and self.role != "finance") or self.is_admin:
            compact_controls = ctk.CTkFrame(layout_parent, fg_color="transparent", corner_radius=0)
            compact_controls.pack(fill="x", padx=12, pady=(8, 4))
            self._compact_controls = compact_controls

        if show_switches:
            if self.role == "finance" and self.finance_banner_tabs is not None:
                left_controls = self.finance_banner_tabs
            else:
                left_controls = ctk.CTkFrame(compact_controls, fg_color="transparent", corner_radius=0)
                left_controls.pack(side="left")

            for tab_name in ("Invoices", "Payments", "Reports"):
                if tab_name not in self.enabled_tabs:
                    continue
                btn = ctk.CTkButton(
                    left_controls,
                    text=tab_name,
                    command=lambda target=tab_name: self._select_tab_by_name(target),
                    fg_color="#FCFAF6",
                    text_color="#4E3E24",
                    hover_color="#E7D6B9",
                    border_width=1,
                    border_color="#D7C5A9",
                    height=40,
                    width=112,
                    corner_radius=18,
                    font=("Arial", 13, "bold"),
                )
                btn.pack(side="left", padx=(0, 8))
                self.tab_switch_buttons[tab_name] = btn

        if self.is_admin and compact_controls is not None:
            right_controls = ctk.CTkFrame(compact_controls, fg_color="transparent", corner_radius=0)
            right_controls.pack(side="right", padx=(0, 12))
            self._admin_top_city_controls = right_controls

            city_options = ["All Cities"] + sorted(
                {str(loc["city"]).strip() for loc in LocationDAO.get_all_locations() if str(loc["city"]).strip()}
            )
            default_city = self.selected_city if self.selected_city in city_options else "All Cities"
            self.city_filter_var = tk.StringVar(value=default_city)
            self.city_filter_menu = ctk.CTkOptionMenu(
                right_controls,
                values=city_options,
                variable=self.city_filter_var,
                command=self._on_city_filter_change,
                width=180,
                height=30,
                corner_radius=12,
                fg_color="#EFE5D3",
                button_color="#D9C8AA",
                button_hover_color="#CDB58E",
                text_color="#3A3123",
                dropdown_fg_color="#FCFAF6",
                dropdown_hover_color="#EFE5D3",
                dropdown_text_color="#3A3123",
                font=("Arial", 12, "bold"),
            )
            self.city_filter_menu.pack(side="left", padx=(0, 0), pady=0)

        self.tab_container = ctk.CTkFrame(layout_parent, fg_color="transparent", corner_radius=0)
        self.tab_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        if "Invoices" in self.enabled_tabs:
            self.invoice_tab = ctk.CTkFrame(self.tab_container, fg_color="transparent", corner_radius=0)
            self._build_invoice_tab()

        if "Payments" in self.enabled_tabs:
            self.payment_tab = ctk.CTkFrame(self.tab_container, fg_color="transparent", corner_radius=0)
            self._build_payment_tab()

        if "Reports" in self.enabled_tabs:
            self.report_tab = ctk.CTkFrame(self.tab_container, fg_color="transparent", corner_radius=0)
            self._build_report_tab()

    def _build_finance_identity_banner(self, parent):
        user_row = AuthController.current_user
        full_name = "Finance Staff"
        location_name = AuthController.get_current_location() or "All Cities"
        try:
            if user_row and user_row["full_name"]:
                full_name = str(user_row["full_name"]).strip()
        except Exception:
            full_name = "Finance Staff"

        hello_name = full_name.split()[0] if full_name else "Finance"
        office_text = str(location_name).strip() or "All Cities"
        if office_text.lower() not in {"all cities", "all locations"} and not office_text.lower().endswith("office"):
            office_text = f"{office_text} Office"

        banner = ctk.CTkFrame(
            parent,
            fg_color="#1F1A12",
            corner_radius=18,
            border_width=1,
            border_color="#312817",
            height=118,   
        )
        banner.pack(fill="x", padx=12, pady=(8, 4))
        banner.pack_propagate(False)

        inner = ctk.CTkFrame(banner, fg_color="transparent", corner_radius=0)
        inner.pack(fill="both", expand=True, padx=20, pady=14)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=0)
        inner.grid_rowconfigure(0, weight=1)

        left_box = ctk.CTkFrame(inner, fg_color="transparent", corner_radius=0)
        left_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            left_box,
            text=f"Good morning, {hello_name} ✨",
            text_color="#D4AF4D",
            font=("Georgia", 22, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))   # more space between title and subtitle

        self.finance_banner_tabs = ctk.CTkFrame(inner, fg_color="transparent", corner_radius=0)
        self.finance_banner_tabs.grid(row=0, column=1, sticky="e")

        # keep the right-side buttons centered vertically
        self.finance_banner_tabs.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            banner,
            text=f"{office_text} - Finance Team",
            text_color="#D8C7A8",
            font=("Arial", 14, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(0, 12))

    def _select_initial_tab(self):
        tab_map = self._tab_map()
        if not tab_map:
            return

        selected_name = self.initial_tab if self.initial_tab in tab_map else next(iter(tab_map))
        self._show_tab(selected_name)
        self._refresh_tab_switch_buttons(selected_name)
        self._update_admin_city_filter_visibility(selected_name)

    def _tab_map(self):
        tab_map = {}
        if hasattr(self, "invoice_tab"):
            tab_map["Invoices"] = self.invoice_tab
        if hasattr(self, "payment_tab"):
            tab_map["Payments"] = self.payment_tab
        if hasattr(self, "report_tab"):
            tab_map["Reports"] = self.report_tab
        return tab_map

    def _show_tab(self, tab_name):
        tab_map = self._tab_map()
        target = tab_map.get(tab_name)
        if target is None:
            return
        for frame in tab_map.values():
            frame.pack_forget()
        target.pack(fill="both", expand=True)

    def _select_tab_by_name(self, tab_name):
        self._show_tab(tab_name)
        self._refresh_tab_switch_buttons(tab_name)
        self._update_admin_city_filter_visibility(tab_name)

    def _update_admin_city_filter_visibility(self, active_tab_name):
        compact_controls = getattr(self, "_compact_controls", None)
        show_switches = bool(getattr(self, "_show_switches", False))
        controls = getattr(self, "_admin_top_city_controls", None)
        is_reports = str(active_tab_name).strip().lower() == "reports"

        if controls is not None:
            if is_reports:
                controls.pack_forget()
            else:
                try:
                    if not controls.winfo_manager():
                        controls.pack(side="right", padx=(0, 12))
                except Exception:
                    pass

        # If no tab-switch buttons are shown, collapse the now-empty row on Reports.
        if compact_controls is not None and not show_switches:
            if is_reports:
                compact_controls.pack_forget()
            else:
                try:
                    if not compact_controls.winfo_manager():
                        compact_controls.pack(fill="x", padx=12, pady=(8, 4))
                except Exception:
                    pass

    def _refresh_tab_switch_buttons(self, active_tab_name):
        if not hasattr(self, "tab_switch_buttons"):
            return
        for tab_name, btn in self.tab_switch_buttons.items():
            is_active = tab_name == active_tab_name
            btn.configure(
                fg_color="#C9A84C" if is_active else "#FCFAF6",
                text_color="#2A2317" if is_active else "#4E3E24",
                hover_color="#B8923E" if is_active else "#E7D6B9",
                border_width=0 if is_active else 1,
                border_color="#C9A84C" if is_active else "#D7C5A9",
            )

    def _build_nav_sections(self):
        sections = [
            {"title": "Overview", "items": []},
            {"title": "Management", "items": []},
            {"title": "Finance", "items": []},
            {"title": "Admin", "items": []},
        ]

        if self.home_callback:
            sections[0]["items"].append(
                {"label": "Dashboard", "action": self.home_callback, "icon": "dashboard"}
            )

        if AuthController.can_access_feature("tenant_management", self.role):
            sections[1]["items"].append(
                {"label": "Tenants", "action": self.open_tenant_management, "icon": "tenants"}
            )
        if AuthController.can_access_feature("apartment_management", self.role):
            sections[1]["items"].append(
                {"label": "Apartments", "action": self.open_apartment_management, "icon": "apartments"}
            )
        if AuthController.can_access_feature("lease_management", self.role):
            sections[1]["items"].append(
                {"label": "Leases", "action": self.open_lease_management, "icon": "leases"}
            )
        if AuthController.can_access_feature("maintenance_management", self.role):
            sections[1]["items"].append(
                {"label": "Maintenance", "action": self.open_maintenance_dashboard, "icon": "maintenance"}
            )

        if AuthController.can_access_feature("finance_dashboard", self.role):
            if self.role == "finance":
                sections[2]["items"].append(
                    {
                        "label": "Payments & Reports",
                        "action": self.open_finance_payments or self._go_payments,
                        "icon": "payments",
                    }
                )
            elif self.role == "manager":
                sections[2]["items"].append(
                    {
                        "label": "Reports",
                        "action": self.open_finance_reports or self._go_reports,
                        "icon": "reports",
                    }
                )
            else:
                sections[2]["items"].append(
                    {
                        "label": "Payments",
                        "action": self.open_finance_payments or self._go_payments,
                        "icon": "payments",
                    }
                )
                sections[2]["items"].append(
                    {
                        "label": "Reports",
                        "action": self.open_finance_reports or self._go_reports,
                        "icon": "reports",
                    }
                )

        sections[3]["items"].append(
            {"label": "User Access", "action": self.open_user_management, "icon": "shield"}
        )
        return sections

    def _go_payments(self):
        self._select_tab_by_name("Payments")

    def _go_invoices(self):
        self._select_tab_by_name("Invoices")

    def _go_reports(self):
        self._select_tab_by_name("Reports")

    def _on_shell_search(self, _text=None):
        if isinstance(_text, str):
            self._search_query = _text.strip()
        elif hasattr(self, "shell") and hasattr(self.shell, "search_var"):
            try:
                self._search_query = str(self.shell.search_var.get() or "").strip()
            except Exception:
                self._search_query = ""

        if hasattr(self, "invoice_tree"):
            self._load_invoice_table()
        if hasattr(self, "payment_tree"):
            self._load_payment_table()
        if hasattr(self, "report_tab"):
            self._load_reports()

    def _matches_search(self, *values):
        query = str(getattr(self, "_search_query", "") or "").strip().lower()
        if not query:
            return True
        haystack = " ".join(str(value or "").strip().lower() for value in values)
        return query in haystack

    @staticmethod
    def _parse_date_text(date_text):
        text = str(date_text or "").strip()
        if not text:
            raise ValueError("empty date")
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"invalid date: {text}")

    @classmethod
    def _to_storage_date(cls, date_text):
        return cls._parse_date_text(date_text).isoformat()

    @classmethod
    def _to_display_date(cls, date_text):
        text = str(date_text or "").strip()
        if not text:
            return ""
        try:
            parsed = cls._parse_date_text(text)
            return parsed.strftime("%d/%m/%Y")
        except ValueError:
            return text

    def _show_alerts(self):
        shell = getattr(self, "shell", None)
        if shell is None or not hasattr(shell, "show_premium_info_modal"):
            messagebox.showinfo("Alerts", "Alerts are available in the dashboard shell view.")
            return

        try:
            open_invoices = InvoiceDAO.get_open_invoices(city=self.city_scope)
        except Exception:
            open_invoices = []
        try:
            late_rows = ReportDAO.get_late_invoices(city=self.city_scope)
        except Exception:
            late_rows = []
        try:
            payments = PaymentDAO.get_all_payments(city=self.city_scope)
        except Exception:
            payments = []

        today = date.today()
        payments_this_month = 0
        for pay in payments:
            raw_date = str(pay.get("payment_date", "")).strip()
            try:
                parsed = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if parsed.year == today.year and parsed.month == today.month:
                payments_this_month += 1

        shell.show_premium_info_modal(
            title="Finance Alerts",
            icon_text="🔔",
            icon_fg="#B8891F",
            icon_bg="#F6E8B8",
            highlight_nonzero=True,
            rows=[
                ("Open invoices", str(len(open_invoices))),
                ("Late payment alerts", str(len(late_rows))),
                ("Payments this month", str(payments_this_month)),
            ],
        )

    def _show_settings(self):
        shell = getattr(self, "shell", None)
        role_text = str(self.role or "").replace("_", " ").title()
        user_name = "User"
        try:
            user_row = AuthController.current_user
            if user_row and user_row["full_name"]:
                user_name = str(user_row["full_name"]).strip()
        except Exception:
            user_name = "User"

        rows = [
            ("User", user_name),
            ("Role", role_text or "Unknown"),
        ]
        if self.is_admin:
            rows.append(("Location Access", "All Cities"))
        else:
            rows.append(("Location", AuthController.get_current_location() or "Unknown"))

        if shell is not None and hasattr(shell, "show_premium_info_modal"):
            shell.show_premium_info_modal(
                title="Account Settings",
                icon_bg="#F6EED7",
                rows=rows,
                icon_image_name="settings",
                icon_image_size=(34, 34),
            )
            return

        messagebox.showinfo("Account Settings", "\n".join(f"{label}: {value}" for label, value in rows))

    # =========================
    # INVOICE TAB
    # =========================
    def _build_invoice_tab(self):
        """
        Build invoice generation form and invoice table.
        """
        style = ttk.Style(self)
        style.configure(
            "Finance.Invoice.Treeview",
            background="#FCFAF6",
            foreground="#2B2418",
            rowheight=40,
            fieldbackground="#FCFAF6",
            borderwidth=0,
            relief="flat",
            font=("Arial", 11),
        )
        style.configure(
            "Finance.Invoice.Treeview.Heading",
            background="#F3ECDF",
            foreground="#7A6748",
            font=("Arial", 11, "bold"),
            relief="flat",
            padding=(8, 8),
        )
        style.layout("Finance.Invoice.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        root = ctk.CTkFrame(self.invoice_tab, fg_color="transparent", corner_radius=0)
        root.pack(fill="both", expand=True)

        form_card = ctk.CTkFrame(
            root,
            fg_color="#FCFAF6",
            corner_radius=16,
            border_width=1,
            border_color="#DDD0BB",
        )
        form_card.pack(fill="x", pady=(0, 10))
        form_card.grid_columnconfigure(0, weight=1)
        form_card.grid_columnconfigure(1, weight=1)
        form_card.grid_columnconfigure(2, weight=1)
        form_card.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            form_card,
            text="Generate Invoice",
            text_color="#2B2418",
            font=("Arial", 22, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=14, pady=(12, 8))

        ctk.CTkLabel(
            form_card,
            text="Lease",
            text_color="#8C7D63",
            font=("Arial", 12, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 4))
        self.lease_combo = ctk.CTkOptionMenu(
            form_card,
            values=["Select lease..."],
            command=self._on_lease_selected,
            width=860,
            height=38,
            corner_radius=12,
            fg_color="#F4ECDE",
            button_color="#D9C8AA",
            button_hover_color="#CDB58E",
            text_color="#3A3123",
            dropdown_fg_color="#FCFAF6",
            dropdown_hover_color="#EFE5D3",
            dropdown_text_color="#3A3123",
            font=("Arial", 12, "bold"),
        )
        self.lease_combo.grid(row=2, column=0, columnspan=4, sticky="ew", padx=14, pady=(0, 10))

        ctk.CTkLabel(form_card, text="Billing Start (DD/MM/YYYY)", text_color="#8C7D63", font=("Arial", 11, "bold")).grid(row=3, column=0, sticky="w", padx=14, pady=(0, 4))
        ctk.CTkLabel(form_card, text="Billing End (DD/MM/YYYY)", text_color="#8C7D63", font=("Arial", 11, "bold")).grid(row=3, column=1, sticky="w", padx=10, pady=(0, 4))
        ctk.CTkLabel(form_card, text="Due Date (DD/MM/YYYY)", text_color="#8C7D63", font=("Arial", 11, "bold")).grid(row=3, column=2, sticky="w", padx=10, pady=(0, 4))
        ctk.CTkLabel(form_card, text="Amount Due", text_color="#8C7D63", font=("Arial", 11, "bold")).grid(row=3, column=3, sticky="w", padx=(10, 14), pady=(0, 4))

        self.billing_start_var = tk.StringVar()
        self.billing_start_var.trace_add(
            "write",
            lambda *_args, target_var=self.billing_start_var: self._on_date_input_change(target_var),
        )
        ctk.CTkEntry(
            form_card,
            textvariable=self.billing_start_var,
            height=36,
            corner_radius=12,
            fg_color="#F4ECDE",
            border_color="#D7C5A9",
            text_color="#3A3123",
            font=("Arial", 12, "bold"),
        ).grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 10))

        self.billing_end_var = tk.StringVar()
        self.billing_end_var.trace_add(
            "write",
            lambda *_args, target_var=self.billing_end_var: self._on_date_input_change(target_var),
        )
        ctk.CTkEntry(
            form_card,
            textvariable=self.billing_end_var,
            height=36,
            corner_radius=12,
            fg_color="#F4ECDE",
            border_color="#D7C5A9",
            text_color="#3A3123",
            font=("Arial", 12, "bold"),
        ).grid(row=4, column=1, sticky="ew", padx=10, pady=(0, 10))

        self.invoice_due_var = tk.StringVar()
        self.invoice_due_var.trace_add(
            "write",
            lambda *_args, target_var=self.invoice_due_var: self._on_date_input_change(target_var),
        )
        ctk.CTkEntry(
            form_card,
            textvariable=self.invoice_due_var,
            height=36,
            corner_radius=12,
            fg_color="#F4ECDE",
            border_color="#D7C5A9",
            text_color="#3A3123",
            font=("Arial", 12, "bold"),
        ).grid(row=4, column=2, sticky="ew", padx=10, pady=(0, 10))

        self.amount_due_var = tk.StringVar()
        ctk.CTkEntry(
            form_card,
            textvariable=self.amount_due_var,
            height=36,
            corner_radius=12,
            fg_color="#F4ECDE",
            border_color="#D7C5A9",
            text_color="#3A3123",
            font=("Arial", 12, "bold"),
        ).grid(row=4, column=3, sticky="ew", padx=(10, 14), pady=(0, 10))

        ctk.CTkButton(
            form_card,
            text="Generate Invoice",
            command=self.create_invoice,
            fg_color="#2A2215",
            text_color="#D4B24F",
            hover_color="#1D170F",
            border_width=1,
            border_color="#A48742",
            height=36,
            corner_radius=14,
            font=("Arial", 12, "bold"),
            width=180,
        ).grid(row=5, column=3, sticky="e", padx=(10, 14), pady=(0, 12))

        list_card = ctk.CTkFrame(
            root,
            fg_color="#FCFAF6",
            corner_radius=16,
            border_width=1,
            border_color="#DDD0BB",
        )
        list_card.pack(fill="both", expand=True)
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            list_card,
            text="All Invoices",
            text_color="#2B2418",
            font=("Arial", 22, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        ctk.CTkButton(
            list_card,
            text="Download Selected Invoice PDF",
            command=self.export_selected_invoice_pdf,
            fg_color="#F3E7D1",
            text_color="#4E3E24",
            hover_color="#E7D6B9",
            border_width=1,
            border_color="#D7C5A9",
            height=34,
            corner_radius=16,
            font=("Arial", 12, "bold"),
        ).grid(row=1, column=0, sticky="e", padx=14, pady=(0, 8))

        ctk.CTkFrame(list_card, fg_color="#E8DEC8", height=1, corner_radius=0).grid(
            row=2, column=0, sticky="ew", padx=14, pady=(0, 8)
        )

        table_wrap = ctk.CTkFrame(
            list_card,
            fg_color="#FCFAF6",
            corner_radius=14,
            border_width=1,
            border_color="#DCCFB9",
        )
        table_wrap.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 12))
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        columns = ("invoiceID", "tenant_name", "city", "period", "due_date", "amount_due", "status")
        self.invoice_tree = ttk.Treeview(
            table_wrap,
            columns=columns,
            show="headings",
            height=11,
            style="Finance.Invoice.Treeview",
        )

        self.invoice_tree.heading("invoiceID", text="Invoice ID", anchor="center")
        self.invoice_tree.heading("tenant_name", text="Tenant", anchor="w")
        self.invoice_tree.heading("city", text="City", anchor="w")
        self.invoice_tree.heading("period", text="Billing Period", anchor="w")
        self.invoice_tree.heading("due_date", text="Due Date", anchor="center")
        self.invoice_tree.heading("amount_due", text="Amount Due", anchor="e")
        self.invoice_tree.heading("status", text="Status", anchor="center")

        self.invoice_tree.column("invoiceID", width=100, minwidth=85, stretch=False, anchor="center")
        self.invoice_tree.column("tenant_name", width=220, minwidth=170, stretch=True, anchor="w")
        self.invoice_tree.column("city", width=150, minwidth=120, stretch=True, anchor="w")
        self.invoice_tree.column("period", width=300, minwidth=220, stretch=True, anchor="w")
        self.invoice_tree.column("due_date", width=120, minwidth=105, stretch=False, anchor="center")
        self.invoice_tree.column("amount_due", width=120, minwidth=100, stretch=False, anchor="e")
        self.invoice_tree.column("status", width=95, minwidth=85, stretch=False, anchor="center")
        self.invoice_tree.grid(row=0, column=0, sticky="nsew")
        self.invoice_tree.configure(yscrollcommand=lambda *_args: None)

    # =========================
    # PAYMENT TAB
    # =========================
    def _build_payment_tab(self):
        """
        Build styled payment workspace inspired by the reference design.
        """
        ctk.set_appearance_mode("light")
        style = ttk.Style(self)
        style.configure(
            "Finance.Treeview",
            background="#EDF0EC",
            foreground="#2B2418",
            rowheight=44,
            fieldbackground="#EDF0EC",
            borderwidth=0,
            relief="flat",
            font=("Arial", 10),
        )
        style.configure(
            "Finance.Treeview.Heading",
            background="#F3ECDF",
            foreground="#7A6748",
            font=("Arial", 10, "bold"),
            relief="flat",
            padding=(10, 10),
        )
        style.layout("Finance.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure(
            "Finance.Late.Treeview",
            background="#EDF0EC",
            foreground="#2B2418",
            rowheight=40,
            fieldbackground="#EDF0EC",
            borderwidth=0,
            relief="flat",
            font=("Arial", 10),
        )
        style.configure(
            "Finance.Late.Treeview.Heading",
            background="#F3ECDF",
            foreground="#7A6748",
            font=("Arial", 10, "bold"),
            relief="flat",
            padding=(10, 10),
        )
        style.layout("Finance.Late.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        self.payment_filter_var = tk.StringVar(value="ALL")
        self.summary_collected_var = tk.StringVar(value="£0")
        self.summary_pending_var = tk.StringVar(value="£0")
        self.summary_late_var = tk.StringVar(value="£0")
        self.summary_late_note_var = tk.StringVar(value="0 invoices overdue")
        self.receipt_map = {}
        self.payment_filter_buttons = {}
        self.late_reminder_sent_keys = set()

        payment_scroll = ctk.CTkScrollableFrame(
            self.payment_tab,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#D9C8AA",
            scrollbar_button_hover_color="#CDB58E",
        )
        payment_scroll.pack(fill="both", expand=True)

        summary_row = ctk.CTkFrame(payment_scroll, fg_color="transparent", corner_radius=0)
        summary_row.pack(fill="x", pady=(0, 10))
        for idx in range(3):
            summary_row.grid_columnconfigure(idx, weight=1)

        self._build_payment_metric_card(
            summary_row,
            0,
            "COLLECTED THIS MONTH",
            self.summary_collected_var,
            "Based on payment date in current month",
        )
        self._build_payment_metric_card(
            summary_row,
            1,
            "PENDING / OVERDUE",
            self.summary_pending_var,
            "Outstanding invoice balance",
            value_color="#8A2525",
        )
        self._build_payment_metric_card(
            summary_row,
            2,
            "LATE AMOUNT",
            self.summary_late_var,
            variable_note=self.summary_late_note_var,
        )

        body = ctk.CTkFrame(payment_scroll, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=0)

        main_card = ctk.CTkFrame(
            body,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        main_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        main_card.grid_columnconfigure(0, weight=1)
        main_card.grid_rowconfigure(3, weight=1)

        action_row = ctk.CTkFrame(main_card, fg_color="transparent", corner_radius=0)
        action_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(2, 8))
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            action_row,
            text="Invoice & Payment Log",
            text_color="#2B2418",
            font=("Arial", 24, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        filter_group = ctk.CTkFrame(action_row, fg_color="transparent", corner_radius=0)
        filter_group.grid(row=0, column=1, sticky="e")
        for label, key in (("All", "ALL"), ("Paid", "PAID"), ("Pending", "PENDING"), ("Overdue", "OVERDUE")):
            btn = ctk.CTkButton(
                filter_group,
                text=label,
                command=lambda status_key=key: self._set_payment_filter(status_key),
                fg_color="#FCFAF6",
                text_color="#5D4D33",
                hover_color="#E7D6B9",
                border_width=1,
                border_color="#D7C5A9",
                width=86,
                height=34,
                corner_radius=18,
                font=("Arial", 12, "bold"),
            )
            btn.pack(side="left", padx=(0, 6))
            self.payment_filter_buttons[key] = btn

        self._refresh_payment_filter_buttons()

        divider = ctk.CTkFrame(main_card, fg_color="#E8DEC8", height=1, corner_radius=0)
        divider.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        form = ctk.CTkFrame(main_card, fg_color="transparent", corner_radius=0)
        form.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 12))
        form.grid_columnconfigure(0, weight=5)
        form.grid_columnconfigure(1, weight=2)
        form.grid_columnconfigure(2, weight=2)
        form.grid_columnconfigure(3, weight=2)
        form.grid_columnconfigure(4, weight=3)

        ctk.CTkLabel(form, text="Open Invoice", text_color="#8C7D63", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4))
        ctk.CTkLabel(form, text="Payment Date (DD/MM/YYYY)", text_color="#8C7D63", font=("Arial", 11, "bold")).grid(row=0, column=1, sticky="w", padx=(10, 8), pady=(0, 4))
        ctk.CTkLabel(form, text="Amount", text_color="#8C7D63", font=("Arial", 11, "bold")).grid(row=0, column=2, sticky="w", padx=(10, 8), pady=(0, 4))
        ctk.CTkLabel(form, text="Method", text_color="#8C7D63", font=("Arial", 11, "bold")).grid(row=0, column=3, sticky="w", padx=(10, 8), pady=(0, 4))

        self.open_invoice_var = tk.StringVar(value="Select invoice...")
        self.open_invoice_menu = ctk.CTkOptionMenu(
            form,
            values=["Select invoice..."],
            variable=self.open_invoice_var,
            command=self._on_invoice_selected_for_payment,
            width=420,
            height=36,
            corner_radius=12,
            fg_color="#F4ECDE",
            button_color="#D9C8AA",
            button_hover_color="#CDB58E",
            text_color="#3A3123",
            dropdown_fg_color="#FCFAF6",
            dropdown_hover_color="#EFE5D3",
            dropdown_text_color="#3A3123",
            font=("Arial", 12, "bold"),
        )
        self.open_invoice_menu.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=0)

        self.payment_date_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        self.payment_date_var.trace_add(
            "write",
            lambda *_args, target_var=self.payment_date_var: self._on_date_input_change(target_var),
        )
        self.payment_date_entry = ctk.CTkEntry(
            form,
            textvariable=self.payment_date_var,
            width=130,
            height=36,
            corner_radius=12,
            fg_color="#F4ECDE",
            border_color="#D7C5A9",
            text_color="#3A3123",
            font=("Arial", 12, "bold"),
        )
        self.payment_date_entry.grid(row=1, column=1, sticky="ew", padx=(10, 8), pady=0)

        self.amount_paid_var = tk.StringVar()
        self._amount_edit_guard = False
        self.amount_paid_var.trace_add("write", self._on_amount_input_change)
        self.amount_paid_entry = ctk.CTkEntry(
            form,
            textvariable=self.amount_paid_var,
            width=120,
            height=36,
            corner_radius=12,
            fg_color="#F4ECDE",
            border_color="#D7C5A9",
            text_color="#3A3123",
            font=("Arial", 12, "bold"),
        )
        self.amount_paid_entry.grid(row=1, column=2, sticky="ew", padx=(10, 8), pady=0)

        self.payment_method_var = tk.StringVar(value="MANUAL")
        self.payment_method_menu = ctk.CTkOptionMenu(
            form,
            values=["MANUAL", "CASH", "BANK_TRANSFER", "CARD"],
            variable=self.payment_method_var,
            width=150,
            height=36,
            corner_radius=12,
            fg_color="#F4ECDE",
            button_color="#D9C8AA",
            button_hover_color="#CDB58E",
            text_color="#3A3123",
            dropdown_fg_color="#FCFAF6",
            dropdown_hover_color="#EFE5D3",
            dropdown_text_color="#3A3123",
            font=("Arial", 12, "bold"),
        )
        self.payment_method_menu.grid(row=1, column=3, sticky="ew", padx=(10, 8), pady=0)

        ctk.CTkButton(
            form,
            text="Record Payment",
            command=self.record_payment,
            fg_color="#2A2215",
            text_color="#D4B24F",
            hover_color="#1D170F",
            border_width=1,
            border_color="#A48742",
            height=34,
            corner_radius=14,
            font=("Arial", 12, "bold"),
        ).grid(row=1, column=4, sticky="ew", padx=(10, 0), pady=0)

        table_card = ctk.CTkFrame(
            main_card,
            fg_color="#F3ECDF",
            corner_radius=16,
            border_width=1,
            border_color="#DCCFB9",
        )
        table_card.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 12))
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(0, weight=1)

        tree_wrap = ctk.CTkFrame(table_card, fg_color="#EDF0EC", corner_radius=0)
        tree_wrap.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        tree_wrap.grid_columnconfigure(0, weight=1)
        tree_wrap.grid_rowconfigure(0, weight=1)

        columns = (
            "paymentID",
            "tenant_name",
            "city",
            "payment_date",
            "amount_paid",
            "payment_method",
            "receipt_number",
            "invoice_status",
        )
        self.payment_tree = ttk.Treeview(tree_wrap, columns=columns, show="headings", height=8, style="Finance.Treeview")
        self.payment_tree.heading("paymentID", text="Payment ID", anchor="center")
        self.payment_tree.heading("tenant_name", text="Tenant", anchor="w")
        self.payment_tree.heading("city", text="City", anchor="w")
        self.payment_tree.heading("payment_date", text="Date", anchor="center")
        self.payment_tree.heading("amount_paid", text="Amount", anchor="e")
        self.payment_tree.heading("payment_method", text="Method", anchor="w")
        self.payment_tree.heading("receipt_number", text="Receipt", anchor="w")
        self.payment_tree.heading("invoice_status", text="Invoice", anchor="center")

        self.payment_tree.column("paymentID", width=140, minwidth=130, stretch=False, anchor="center")
        self.payment_tree.column("tenant_name", width=280, minwidth=220, stretch=True, anchor="w")
        self.payment_tree.column("city", width=180, minwidth=140, stretch=True, anchor="w")
        self.payment_tree.column("payment_date", width=150, minwidth=130, stretch=False, anchor="center")
        self.payment_tree.column("amount_paid", width=140, minwidth=120, stretch=False, anchor="e")
        self.payment_tree.column("payment_method", width=210, minwidth=170, stretch=True, anchor="w")
        self.payment_tree.column("receipt_number", width=300, minwidth=230, stretch=True, anchor="w")
        self.payment_tree.column("invoice_status", width=120, minwidth=100, stretch=False, anchor="center")
        self.payment_tree.grid(row=0, column=0, sticky="nsew")
        self.payment_tree.bind("<<TreeviewSelect>>", self._on_payment_tree_select)
        self.payment_tree.tag_configure("row_paid", background="#F4F8F3")
        self.payment_tree.tag_configure("row_overdue", background="#FDF2F2")
        self.payment_tree.tag_configure("row_pending", background="#FFF9EF")

        # Keep the log clean: hide the dedicated vertical scrollbar.
        self.payment_tree.configure(yscrollcommand=lambda *_args: None)

        bottom_panels = ctk.CTkFrame(body, fg_color="transparent", corner_radius=0)
        bottom_panels.grid(row=1, column=0, sticky="ew", pady=(4, 6))
        bottom_panels.grid_columnconfigure(0, weight=3)
        bottom_panels.grid_columnconfigure(1, weight=2)

        alerts_card = ctk.CTkFrame(
            bottom_panels,
            fg_color="#FCFAF6",
            corner_radius=14,
            border_width=1,
            border_color="#DDD0BB",
        )
        alerts_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        alerts_card.grid_rowconfigure(2, weight=1)
        alerts_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            alerts_card,
            text="Late Payment Alerts",
            text_color="#2B2418",
            font=("Arial", 24, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 2))

        late_actions = ctk.CTkFrame(alerts_card, fg_color="transparent", corner_radius=0)
        late_actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        ctk.CTkButton(
            late_actions,
            text="Send Reminder",
            command=self._send_late_payment_reminder,
            fg_color="#F3E7D1",
            text_color="#4E3E24",
            hover_color="#E7D6B9",
            border_width=1,
            border_color="#D7C5A9",
            height=32,
            corner_radius=14,
            font=("Arial", 12, "bold"),
        ).pack(side="right")

        late_table_card = ctk.CTkFrame(
            alerts_card,
            fg_color="#F3ECDF",
            corner_radius=14,
            border_width=1,
            border_color="#DCCFB9",
        )
        late_table_card.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        late_table_card.grid_rowconfigure(0, weight=1)
        late_table_card.grid_columnconfigure(0, weight=1)

        late_tree_wrap = ctk.CTkFrame(late_table_card, fg_color="#EDF0EC", corner_radius=0)
        late_tree_wrap.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        late_tree_wrap.grid_rowconfigure(0, weight=1)
        late_tree_wrap.grid_columnconfigure(0, weight=1)

        late_cols = ("tenant_name", "due_date", "outstanding")
        self.payment_late_tree = ttk.Treeview(
            late_tree_wrap,
            columns=late_cols,
            show="headings",
            height=7,
            style="Finance.Late.Treeview",
        )
        self.payment_late_tree.heading("tenant_name", text="Tenant / Unit")
        self.payment_late_tree.heading("due_date", text="Due Date")
        self.payment_late_tree.heading("outstanding", text="Outstanding")
        self.payment_late_tree.column("tenant_name", width=280, minwidth=220, stretch=True, anchor="w")
        self.payment_late_tree.column("due_date", width=140, minwidth=120, stretch=False, anchor="center")
        self.payment_late_tree.column("outstanding", width=150, minwidth=120, stretch=False, anchor="e")
        self.payment_late_tree.grid(row=0, column=0, sticky="nsew")

        # Keep late alert panel visually clean; hide dedicated vertical scrollbar.
        self.payment_late_tree.configure(yscrollcommand=lambda *_args: None)

        receipt_card = ctk.CTkFrame(
            bottom_panels,
            fg_color="#FCFAF6",
            corner_radius=14,
            border_width=1,
            border_color="#DDD0BB",
        )
        receipt_card.grid(row=0, column=1, sticky="new")
        receipt_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            receipt_card,
            text="Generate Receipt",
            text_color="#2B2418",
            font=("Arial", 18, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(10, 2), padx=10)

        ctk.CTkLabel(
            receipt_card,
            text="Choose a payment to export receipt PDF.",
            text_color="#8C7D63",
            font=("Arial", 10),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(0, 6), padx=10)

        self.receipt_var = tk.StringVar(value="Select payment...")
        self.receipt_combo = ctk.CTkOptionMenu(
            receipt_card,
            values=["Select payment..."],
            variable=self.receipt_var,
            width=260,
            height=38,
            corner_radius=12,
            fg_color="#F4ECDE",
            button_color="#D9C8AA",
            button_hover_color="#CDB58E",
            text_color="#3A3123",
            dropdown_fg_color="#FCFAF6",
            dropdown_hover_color="#EFE5D3",
            dropdown_text_color="#3A3123",
            font=("Arial", 12, "bold"),
        )
        self.receipt_combo.grid(row=2, column=0, sticky="ew", pady=(0, 6), padx=10)

        ctk.CTkButton(
            receipt_card,
            text="Generate Billing Receipt",
            command=self._export_receipt_from_combo,
            fg_color="#2A2215",
            text_color="#D4B24F",
            hover_color="#1D170F",
            border_width=1,
            border_color="#A48742",
            height=36,
            corner_radius=14,
            font=("Arial", 13, "bold"),
        ).grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

    def _on_amount_input_change(self, *_args):
        if getattr(self, "_amount_edit_guard", False):
            return
        text = str(self.amount_paid_var.get() or "")
        cleaned_chars = []
        seen_dot = False
        for ch in text:
            if ch.isdigit():
                cleaned_chars.append(ch)
            elif ch == "." and not seen_dot:
                cleaned_chars.append(ch)
                seen_dot = True
        cleaned = "".join(cleaned_chars)
        if cleaned != text:
            self._amount_edit_guard = True
            self.amount_paid_var.set(cleaned)
            self._amount_edit_guard = False

    def _on_date_input_change(self, target_var):
        if getattr(self, "_date_edit_guard", False):
            return
        text = str(target_var.get() or "")
        digits = "".join(ch for ch in text if ch.isdigit())[:8]
        parts = []
        if digits:
            parts.append(digits[:2])
        if len(digits) > 2:
            parts.append(digits[2:4])
        if len(digits) > 4:
            parts.append(digits[4:8])
        cleaned = "/".join(parts)
        if cleaned != text:
            self._date_edit_guard = True
            target_var.set(cleaned)
            self._date_edit_guard = False

    def _build_payment_metric_card(
        self,
        parent,
        column,
        title,
        value_variable,
        note_text=None,
        variable_note=None,
        value_color="#2B2418",
    ):
        card = ctk.CTkFrame(
            parent,
            fg_color="#FCFAF6",
            corner_radius=14,
            border_width=1,
            border_color="#DDD0BB",
        )
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 8) if column < 2 else 0)
        ctk.CTkLabel(
            card,
            text=title,
            text_color="#8C7D63",
            font=("Arial", 11, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(12, 2))
        ctk.CTkLabel(
            card,
            textvariable=value_variable,
            text_color=value_color,
            font=("Georgia", 32, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=12)
        if variable_note is not None:
            ctk.CTkLabel(
                card,
                textvariable=variable_note,
                text_color="#8C7D63",
                font=("Arial", 11),
                anchor="w",
            ).pack(anchor="w", padx=12, pady=(0, 12))
        else:
            ctk.CTkLabel(
                card,
                text=note_text or "",
                text_color="#8C7D63",
                font=("Arial", 11),
                anchor="w",
            ).pack(anchor="w", padx=12, pady=(0, 12))

    def _set_payment_filter(self, status_key):
        self.payment_filter_var.set(status_key)
        self._refresh_payment_filter_buttons()
        self._load_payment_table()

    def _refresh_payment_filter_buttons(self):
        active = str(self.payment_filter_var.get()).strip().upper() or "ALL"
        for key, btn in self.payment_filter_buttons.items():
            is_active = key == active
            btn.configure(
                fg_color="#C9A84C" if is_active else "#FCFAF6",
                text_color="#2A2317" if is_active else "#5D4D33",
                hover_color="#B8923E" if is_active else "#E7D6B9",
                border_width=0 if is_active else 1,
                border_color="#C9A84C" if is_active else "#D7C5A9",
            )

    def _on_payment_tree_select(self, _event=None):
        selected = self.payment_tree.selection()
        if not selected:
            return
        row = self.payment_tree.item(selected[0], "values")
        if not row:
            return
        selected_id = str(row[0]).strip()
        for label, payment_id in self.receipt_map.items():
            if str(payment_id) == selected_id:
                self.receipt_combo.set(label)
                break

    def _export_receipt_from_combo(self):
        selected_label = str(self.receipt_combo.get()).strip()
        payment_id = self.receipt_map.get(selected_label)
        if payment_id is None:
            messagebox.showwarning("No Selection", "Please select a payment first.")
            return
        self._export_payment_pdf_by_id(int(payment_id))

    def _send_late_payment_reminder(self):
        if not hasattr(self, "payment_late_tree"):
            return

        rows = self.payment_late_tree.get_children()
        if not rows:
            self._show_late_reminder_popup("No late payment alerts to remind right now.")
            return

        selected = self.payment_late_tree.selection()
        target_rows = list(selected) if selected else list(rows)
        if not selected:
            send_all = messagebox.askyesno(
                "Send Reminder",
                "No row selected.\nSend reminders to all listed late alerts?",
            )
            if not send_all:
                return

        new_count = 0
        already_sent = 0
        for item_id in target_rows:
            values = self.payment_late_tree.item(item_id, "values")
            if not values:
                continue
            reminder_key = tuple(str(v).strip() for v in values)
            if reminder_key in self.late_reminder_sent_keys:
                already_sent += 1
                continue
            self.late_reminder_sent_keys.add(reminder_key)
            new_count += 1

        if new_count == 0 and already_sent > 0:
            self._show_late_reminder_popup("Reminder already sent for the selected alert(s).")
            return

        if already_sent > 0:
            self._show_late_reminder_popup(
                f"Sent {new_count} reminder(s). Skipped {already_sent} already sent."
            )
            return

        self._show_late_reminder_popup(f"Sent {new_count} reminder(s) successfully.")

    def _show_late_reminder_popup(self, message_text):
        shell = getattr(self, "shell", None)
        if shell is not None and hasattr(shell, "show_premium_info_modal"):
            shell.show_premium_info_modal(
                title="Late Payment Alerts",
                rows=[("", message_text)],
                button_text="OK",
                icon_image_name="latepayment",
                icon_image_size=(38, 38),
            )
            return

        # Fallback for contexts where premium shell is unavailable.
        messagebox.showinfo("Late Payment Alerts", message_text)

    def _show_success_popup(self, message_text, title="Success"):
        shell = getattr(self, "shell", None)
        if shell is not None and hasattr(shell, "show_premium_info_modal"):
            shell.show_premium_info_modal(
                title=title,
                rows=[("", message_text)],
                button_text="OK",
                icon_image_name="success",
                icon_image_size=(38, 38),
            )
            return
        messagebox.showinfo(title, message_text)

    def _refresh_payment_metrics_and_alerts(self):
        summary = ReportDAO.get_overall_financial_summary(city=self.city_scope)
        late_rows = ReportDAO.get_late_invoices(city=self.city_scope)

        today = date.today()
        month_collected = 0.0
        for pay in PaymentDAO.get_all_payments(city=self.city_scope):
            pay_date = str(pay.get("payment_date", "")).strip()
            try:
                parsed = datetime.strptime(pay_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if parsed.year == today.year and parsed.month == today.month:
                month_collected += float(pay.get("amount_paid", 0) or 0)

        late_outstanding = sum(float(row.get("outstanding_balance", 0) or 0) for row in late_rows)
        self.summary_collected_var.set(f"£{month_collected:,.0f}")
        self.summary_pending_var.set(f"£{float(summary['total_pending']):,.0f}")
        self.summary_late_var.set(f"£{late_outstanding:,.0f}")
        self.summary_late_note_var.set(f"{len(late_rows)} invoices overdue")

        for item in self.payment_late_tree.get_children():
            self.payment_late_tree.delete(item)
        for row in late_rows[:25]:
            if not self._matches_search(
                row.get("invoiceID"),
                row.get("tenant_name", "Unknown"),
                row.get("city", ""),
                row.get("due_date", ""),
                row.get("outstanding_balance", 0),
            ):
                continue
            self.payment_late_tree.insert(
                "",
                "end",
                values=(
                    row.get("tenant_name", "Unknown"),
                    self._to_display_date(row.get("due_date", "")),
                    f"{float(row.get('outstanding_balance', 0) or 0):.2f}",
                ),
            )

    # =========================
    # REPORT TAB
    # =========================
    def _build_report_tab(self):
        self.report_city_buttons = {}
        self.report_city_filter_var = tk.StringVar(value="All Cities" if self.is_admin else (self.city_scope or "All Cities"))
        self.report_occupancy_rate_var = tk.StringVar(value="0%")
        self.report_occupancy_note_var = tk.StringVar(value="0 of 0 units occupied")
        self.report_rent_var = tk.StringVar(value="£0")
        self.report_rent_note_var = tk.StringVar(value="£0 pending this month")
        self.report_maintenance_var = tk.StringVar(value="£0")
        self.report_maintenance_note_var = tk.StringVar(value="Budget £8,000 - 0% used")
        self.report_collected_box_var = tk.StringVar(value="£0")
        self.report_pending_box_var = tk.StringVar(value="£0")
        self.report_month_chart_canvas = None

        report_scroll = ctk.CTkScrollableFrame(
            self.report_tab,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#D9C8AA",
            scrollbar_button_hover_color="#CDB58E",
        )
        report_scroll.pack(fill="both", expand=True)

        top_actions = ctk.CTkFrame(report_scroll, fg_color="transparent", corner_radius=0)
        top_actions.pack(fill="x", pady=(0, 10))
        top_actions.grid_columnconfigure(0, weight=1)
        top_actions.grid_columnconfigure(1, weight=0)

        self.report_city_chips = ctk.CTkFrame(top_actions, fg_color="transparent", corner_radius=0)
        self.report_city_chips.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            top_actions,
            text="Export PDF Report",
            command=self.export_reports_pdf,
            fg_color="#FCFAF6",
            text_color="#26201A",
            hover_color="#EFE5D3",
            border_width=1,
            border_color="#C8B79A",
            corner_radius=16,
            width=220,
            height=54,
            font=("Arial", 20, "bold"),
        ).grid(row=0, column=1, sticky="e", padx=(12, 0))

        summary_row = ctk.CTkFrame(report_scroll, fg_color="transparent", corner_radius=0)
        summary_row.pack(fill="x", pady=(0, 12))
        for idx in range(3):
            summary_row.grid_columnconfigure(idx, weight=1)

        self._build_report_metric_card(
            summary_row,
            0,
            "OCCUPANCY RATE",
            self.report_occupancy_rate_var,
            self.report_occupancy_note_var,
        )
        self._build_report_metric_card(
            summary_row,
            1,
            "RENT COLLECTED VS PENDING",
            self.report_rent_var,
            self.report_rent_note_var,
        )
        self._build_report_metric_card(
            summary_row,
            2,
            "MAINTENANCE SPEND YTD",
            self.report_maintenance_var,
            self.report_maintenance_note_var,
        )

        middle_row = ctk.CTkFrame(report_scroll, fg_color="transparent", corner_radius=0)
        middle_row.pack(fill="x", pady=(0, 12))
        middle_row.grid_columnconfigure(0, weight=5)
        middle_row.grid_columnconfigure(1, weight=6)

        collection_card = ctk.CTkFrame(middle_row, fg_color="#FCFAF6", corner_radius=16, border_width=1, border_color="#DDD0BB")
        collection_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        collection_card.grid_columnconfigure(0, weight=1)

        header_left = ctk.CTkFrame(collection_card, fg_color="transparent", corner_radius=0, height=56)
        header_left.grid(row=0, column=0, sticky="ew")
        header_left.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header_left, text="Monthly Rent Collection", text_color="#2B2418", font=("Arial", 18, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(10, 6))
        ctk.CTkLabel(header_left, text="Last 6 months", text_color="#9A7A2E", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="e", padx=18, pady=(12, 8))
        ctk.CTkFrame(collection_card, fg_color="#E8DEC8", height=1, corner_radius=0).grid(row=1, column=0, sticky="ew")

        self.report_month_bar_container = ctk.CTkFrame(collection_card, fg_color="transparent", corner_radius=0)
        self.report_month_bar_container.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 6))

        totals_row = ctk.CTkFrame(collection_card, fg_color="transparent", corner_radius=0)
        totals_row.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 8))
        totals_row.grid_columnconfigure(0, weight=1)
        totals_row.grid_columnconfigure(1, weight=1)
        collected_box = ctk.CTkFrame(totals_row, fg_color="#E4ECE3", corner_radius=12, height=72)
        collected_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(collected_box, text="Collected", text_color="#2F6C3B", font=("Arial", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 1))
        ctk.CTkLabel(collected_box, textvariable=self.report_collected_box_var, text_color="#2B2418", font=("Georgia", 24, "bold")).pack(anchor="w", padx=14, pady=(0, 8))
        pending_box = ctk.CTkFrame(totals_row, fg_color="#EFE4E4", corner_radius=12, height=72)
        pending_box.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(pending_box, text="Pending", text_color="#9C2D2D", font=("Arial", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 1))
        ctk.CTkLabel(pending_box, textvariable=self.report_pending_box_var, text_color="#2B2418", font=("Georgia", 24, "bold")).pack(anchor="w", padx=14, pady=(0, 8))

        occupancy_card = ctk.CTkFrame(middle_row, fg_color="#FCFAF6", corner_radius=16, border_width=1, border_color="#DDD0BB")
        occupancy_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        occupancy_card.grid_columnconfigure(0, weight=1)
        head = ctk.CTkFrame(occupancy_card, fg_color="transparent", corner_radius=0, height=56)
        head.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(head, text="Occupancy by City", text_color="#2B2418", font=("Arial", 20, "bold")).pack(side="left", padx=18, pady=(12, 8))
        ctk.CTkFrame(occupancy_card, fg_color="#E8DEC8", height=1, corner_radius=0).grid(row=1, column=0, sticky="ew")
        self.report_occupancy_list_container = ctk.CTkFrame(occupancy_card, fg_color="transparent", corner_radius=0)
        self.report_occupancy_list_container.grid(row=2, column=0, sticky="ew", padx=14, pady=(8, 12))

        maintenance_card = ctk.CTkFrame(report_scroll, fg_color="#FCFAF6", corner_radius=16, border_width=1, border_color="#DDD0BB")
        maintenance_card.pack(fill="x", pady=(0, 8))
        maintenance_card.grid_columnconfigure(0, weight=1)
        m_head = ctk.CTkFrame(maintenance_card, fg_color="transparent", corner_radius=0, height=56)
        m_head.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(m_head, text="Maintenance Cost Breakdown", text_color="#2B2418", font=("Arial", 20, "bold")).pack(side="left", padx=18, pady=(12, 8))
        ctk.CTkLabel(m_head, text="YTD - Budget £8,000", text_color="#9A7A2E", font=("Arial", 12, "bold")).pack(side="right", padx=18, pady=(12, 8))
        ctk.CTkFrame(maintenance_card, fg_color="#E8DEC8", height=1, corner_radius=0).grid(row=1, column=0, sticky="ew")
        self.report_maintenance_list_container = ctk.CTkFrame(maintenance_card, fg_color="transparent", corner_radius=0)
        self.report_maintenance_list_container.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 14))

        self._rebuild_report_city_chips()
        self._load_reports()

    def _build_report_metric_card(self, parent, col, title, value_var, note_var):
        card = ctk.CTkFrame(parent, fg_color="#FCFAF6", corner_radius=16, border_width=1, border_color="#DDD0BB")
        card.grid(row=0, column=col, sticky="nsew", padx=(0, 8) if col < 2 else 0)
        ctk.CTkLabel(card, text=title, text_color="#8C7D63", font=("Arial", 11, "bold"), justify="left").pack(anchor="w", padx=16, pady=(10, 2))
        ctk.CTkLabel(card, textvariable=value_var, text_color="#2B2418", font=("Georgia", 24, "bold")).pack(anchor="w", padx=16)
        ctk.CTkLabel(card, textvariable=note_var, text_color="#8C7D63", font=("Arial", 10, "bold"), justify="left").pack(anchor="w", padx=16, pady=(0, 12))

    def _rebuild_report_city_chips(self):
        if not hasattr(self, "report_city_chips"):
            return
        for widget in self.report_city_chips.winfo_children():
            widget.destroy()
        self.report_city_buttons = {}

        if self.is_admin:
            cities = sorted({str(loc["city"]).strip() for loc in LocationDAO.get_all_locations() if str(loc["city"]).strip()})
            chip_values = cities + (["All Cities"] if "All Cities" not in cities else [])
        else:
            chip_values = [self.city_scope or "All Cities"]
        if not chip_values:
            chip_values = ["All Cities"]

        current = str(self.report_city_filter_var.get() or "").strip()
        if current not in chip_values:
            current = chip_values[0]
            self.report_city_filter_var.set(current)

        for city_name in chip_values:
            btn = ctk.CTkButton(
                self.report_city_chips,
                text=city_name,
                command=lambda city=city_name: self._set_report_city_filter(city),
                fg_color="#FCFAF6",
                text_color="#5D4D33",
                hover_color="#E7D6B9",
                border_width=1,
                border_color="#D7C5A9",
                width=max(92, len(city_name) * 9),
                height=40,
                corner_radius=20,
                font=("Arial", 12, "bold"),
            )
            btn.pack(side="left", padx=(0, 8))
            self.report_city_buttons[city_name] = btn

        self._refresh_report_city_buttons()

    def _refresh_report_city_buttons(self):
        active = str(self.report_city_filter_var.get() or "").strip()
        for city_name, btn in self.report_city_buttons.items():
            is_active = city_name == active
            btn.configure(
                fg_color="#C9A84C" if is_active else "#FCFAF6",
                text_color="#2A2317" if is_active else "#5D4D33",
                hover_color="#B8923E" if is_active else "#E7D6B9",
                border_width=0 if is_active else 1,
                border_color="#C9A84C" if is_active else "#D7C5A9",
            )

    def _set_report_city_filter(self, city_name):
        self.report_city_filter_var.set(city_name)
        self._refresh_report_city_buttons()
        self._load_reports()

    @staticmethod
    def _format_report_money(value):
        amount = float(value or 0)
        if abs(amount) >= 1000:
            return f"£{amount / 1000:.1f}k"
        return f"£{amount:,.0f}"

    def _effective_report_city_scope(self):
        if hasattr(self, "report_city_filter_var"):
            selected = str(self.report_city_filter_var.get() or "").strip()
        else:
            selected = "All Cities" if self.is_admin else (self.city_scope or "All Cities")
        if self.is_admin:
            if selected and selected.lower() not in {"all cities", "all"}:
                return selected
            return None
        return self.city_scope

    def _build_report_monthly_series(self, payments):
        today = date.today()
        buckets = []
        for offset in range(5, -1, -1):
            month_num = today.month - offset
            year_num = today.year
            while month_num <= 0:
                month_num += 12
                year_num -= 1
            key = f"{year_num:04d}-{month_num:02d}"
            buckets.append({"key": key, "label": datetime(year_num, month_num, 1).strftime("%b"), "total": 0.0})

        bucket_map = {row["key"]: row for row in buckets}
        for payment in payments:
            pay_date_text = str(payment.get("payment_date", "")).strip()
            try:
                parsed = datetime.strptime(pay_date_text, "%Y-%m-%d")
            except ValueError:
                continue
            key = parsed.strftime("%Y-%m")
            if key in bucket_map:
                bucket_map[key]["total"] += float(payment.get("amount_paid", 0) or 0)
        return buckets

    @staticmethod
    def _categorise_maintenance(title_text):
        text = str(title_text or "").strip().lower()
        if any(token in text for token in ("plumb", "pipe", "leak", "drain")):
            return "Plumbing"
        if any(token in text for token in ("elect", "socket", "light", "wiring")):
            return "Electrical"
        if any(token in text for token in ("hvac", "heat", "air", "boiler", "cool")):
            return "Heating / HVAC"
        if any(token in text for token in ("window", "wall", "struct", "door")):
            return "Structural / Windows"
        return "General"
        # =========================
    # REFRESH EVERYTHING
    # =========================
    def refresh_all(self):
        """
        Refresh all dashboard data.
        """
        if hasattr(self, "lease_combo"):
            self._load_lease_options()
        if hasattr(self, "invoice_tree"):
            self._load_invoice_table()
        if hasattr(self, "open_invoice_menu"):
            self._load_open_invoice_options()
        if hasattr(self, "payment_tree"):
            self._load_payment_table()
        if hasattr(self, "report_tab"):
            self._load_reports()

    # =========================
    # LOAD LEASE OPTIONS
    # =========================
    def _load_lease_options(self):
        """
        Load active leases into invoice generation combobox.
        """
        self.lease_map.clear()

        leases = LeaseDAO.get_all_leases_with_financial_details(city=self.city_scope)
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

        if isinstance(getattr(self, "lease_combo", None), ctk.CTkOptionMenu):
            self.lease_combo.configure(values=values or ["No active leases"])
            if values:
                self.lease_combo.set(values[0])
                self._on_lease_selected(values[0])
            else:
                self.lease_combo.set("No active leases")
                self.billing_start_var.set("")
                self.billing_end_var.set("")
                self.invoice_due_var.set("")
                self.amount_due_var.set("")
            return

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
        invoices = InvoiceDAO.get_all_invoices(city=self.city_scope)

        for inv in invoices:
            period = (
                f"{self._to_display_date(inv.get('billing_period_start', ''))} to "
                f"{self._to_display_date(inv.get('billing_period_end', ''))}"
            )
            if not self._matches_search(
                inv.get("invoiceID"),
                inv.get("tenant_name"),
                inv.get("city", "Unknown"),
                period,
                inv.get("due_date"),
                inv.get("amount_due"),
                inv.get("status"),
            ):
                continue
            self.invoice_tree.insert(
                "",
                "end",
                values=(
                    inv["invoiceID"],
                    inv["tenant_name"],
                    inv.get("city", "Unknown"),
                    period,
                    self._to_display_date(inv.get("due_date", "")),
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
        open_invoices = []

        try:
            InvoiceDAO.mark_overdue_invoices()
            open_invoices = InvoiceDAO.get_open_invoices(city=self.city_scope)
        except Exception:
            open_invoices = []

        if not open_invoices:
            # Fallback for legacy/mixed status text so invoices remain payable.
            try:
                all_invoices = InvoiceDAO.get_all_invoices(city=self.city_scope)
            except Exception:
                all_invoices = []

            open_invoices = [
                inv
                for inv in all_invoices
                if str(inv.get("status", "")).strip().upper() != "PAID"
            ]

        values = []
        for inv in open_invoices:
            invoice_id = inv.get("invoiceID")
            if invoice_id is None:
                continue

            try:
                outstanding = InvoiceDAO.get_outstanding_balance(invoice_id)
            except Exception:
                outstanding = float(inv.get("amount_due", 0) or 0)

            tenant_name = inv.get("tenant_name", "Unknown Tenant")
            city_name = inv.get("city", "Unknown")
            status_text = str(inv.get("status", "UNPAID")).strip().upper()

            label = (
                f"Invoice #{invoice_id} | "
                f"{tenant_name} | "
                f"{city_name} | "
                f"Outstanding: {outstanding:.2f} | "
                f"Status: {status_text}"
            )
            self.invoice_map[label] = inv
            values.append(label)

        if hasattr(self, "open_invoice_menu"):
            self.open_invoice_menu.configure(values=values or ["No open invoices"])
            if values:
                self.open_invoice_menu.set(values[0])
                self._on_invoice_selected_for_payment(values[0])
            else:
                self.open_invoice_menu.set("No open invoices")
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

        payments = PaymentDAO.get_all_payments(city=self.city_scope)
        invoice_status_by_id = {}
        try:
            invoices = InvoiceDAO.get_all_invoices(city=self.city_scope)
            invoice_status_by_id = {
                int(inv["invoiceID"]): str(inv.get("status", "")).strip().upper()
                for inv in invoices
                if inv.get("invoiceID") is not None
            }
        except Exception:
            invoice_status_by_id = {}

        filter_key = "ALL"
        if hasattr(self, "payment_filter_var"):
            filter_key = str(self.payment_filter_var.get()).strip().upper() or "ALL"
        self.receipt_map = {}
        receipt_values = []

        for pay in payments:
            invoice_id = pay.get("invoiceID")
            try:
                invoice_id_key = int(invoice_id) if invoice_id is not None else None
            except (TypeError, ValueError):
                invoice_id_key = None
            invoice_status = invoice_status_by_id.get(invoice_id_key, "PAID") if invoice_id_key is not None else "PAID"

            if filter_key == "PAID" and invoice_status != "PAID":
                continue
            if filter_key == "PENDING" and invoice_status not in {"UNPAID", "PARTIAL", "PARTIALLY_PAID"}:
                continue
            if filter_key == "OVERDUE" and invoice_status != "LATE":
                continue
            if not self._matches_search(
                pay.get("paymentID"),
                pay.get("invoiceID"),
                pay.get("tenant_name"),
                pay.get("city", "Unknown"),
                pay.get("payment_date"),
                pay.get("amount_paid"),
                pay.get("payment_method"),
                pay.get("receipt_number"),
                invoice_status,
            ):
                continue

            tag_name = ""
            if invoice_status == "PAID":
                tag_name = "row_paid"
            elif invoice_status == "LATE":
                tag_name = "row_overdue"
            elif invoice_status in {"UNPAID", "PARTIAL", "PARTIALLY_PAID"}:
                tag_name = "row_pending"

            self.payment_tree.insert(
                "",
                "end",
                values=(
                    pay["paymentID"],
                    pay["tenant_name"],
                    pay.get("city", "Unknown"),
                    self._to_display_date(pay.get("payment_date", "")),
                    f"{float(pay['amount_paid']):.2f}",
                    pay["payment_method"],
                    pay["receipt_number"],
                    invoice_status.title(),
                ),
                tags=(tag_name,) if tag_name else (),
            )

            receipt_label = (
                f"#{pay['paymentID']} | {pay.get('tenant_name', 'Unknown')} | "
                f"£{float(pay.get('amount_paid', 0) or 0):.2f} | {self._to_display_date(pay.get('payment_date', ''))}"
            )
            self.receipt_map[receipt_label] = pay["paymentID"]
            receipt_values.append(receipt_label)

        if hasattr(self, "receipt_combo"):
            self.receipt_combo.configure(values=receipt_values or ["Select payment..."])
            current_value = str(self.receipt_combo.get()).strip()
            if receipt_values and current_value not in receipt_values:
                self.receipt_combo.set(receipt_values[0])
            elif not receipt_values:
                self.receipt_combo.set("Select payment...")

        if hasattr(self, "payment_late_tree"):
            self._refresh_payment_metrics_and_alerts()

    # =========================
    # LOAD REPORTS
    # =========================
    def _load_reports(self):
        city_scope = self._effective_report_city_scope()
        summary = ReportDAO.get_overall_financial_summary(city=city_scope)
        occupancy_rows = ReportDAO.get_occupancy_report_by_city()
        if city_scope:
            occupancy_rows = [row for row in occupancy_rows if str(row.get("city", "")).strip() == city_scope]

        payments = PaymentDAO.get_all_payments(city=city_scope)
        monthly = self._build_report_monthly_series(payments)
        total_cost, _total_hours, _resolved_count = MaintenanceDAO.get_cost_report_data(city=city_scope)
        maintenance_requests = MaintenanceDAO.get_all_requests(city=city_scope)

        occupied_total = sum(int(row.get("occupied_apartments", 0) or 0) for row in occupancy_rows)
        apartments_total = sum(int(row.get("total_apartments", 0) or 0) for row in occupancy_rows)
        occ_rate = (occupied_total / apartments_total * 100) if apartments_total else 0

        self.report_occupancy_rate_var.set(f"{occ_rate:.1f}%")
        self.report_occupancy_note_var.set(f"{occupied_total} of {apartments_total} units occupied")
        self.report_rent_var.set(self._format_report_money(summary["total_collected"]))
        self.report_rent_note_var.set(f"{self._format_report_money(summary['total_pending'])} still pending this month")
        self.report_maintenance_var.set(self._format_report_money(total_cost))
        budget = 8000.0
        used_pct = min(100, (total_cost / budget * 100) if budget else 0)
        self.report_maintenance_note_var.set(f"Budget £8,000 - {used_pct:.0f}% used")
        self.report_collected_box_var.set(f"£{float(summary['total_collected']):,.0f}")
        self.report_pending_box_var.set(f"£{float(summary['total_pending']):,.0f}")

        if hasattr(self, "report_month_bar_container"):
            for widget in self.report_month_bar_container.winfo_children():
                widget.destroy()
            if self.report_month_chart_canvas is not None:
                try:
                    self.report_month_chart_canvas.get_tk_widget().destroy()
                except Exception:
                    pass
                self.report_month_chart_canvas = None

            if MATPLOTLIB_AVAILABLE and Figure is not None and FigureCanvasTkAgg is not None:
                labels = [row["label"] for row in monthly]
                values = [float(row["total"] or 0) for row in monthly]
                colors = ["#D7C690"] * max(0, len(values) - 1) + ["#C9A84C"] if values else ["#C9A84C"]

                fig = Figure(figsize=(4.4, 2.0), dpi=120)
                ax = fig.add_subplot(111)
                fig.patch.set_facecolor("#FCFAF6")
                ax.set_facecolor("#FCFAF6")
                bars = ax.bar(labels, values, color=colors, width=0.78, linewidth=0)
                for bar in bars:
                    bar.set_linewidth(0)

                ax.spines["top"].set_visible(False)
                ax.spines["left"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["bottom"].set_color("#E8DEC8")
                ax.tick_params(axis="x", colors="#8C7D63", labelsize=10, length=0)
                ax.tick_params(axis="y", length=0, labelleft=False)
                ymax = max(values) * 1.25 if values and max(values) > 0 else 1
                ax.set_ylim(0, ymax)
                ax.set_yticks([])
                fig.tight_layout(pad=0.6)

                self.report_month_chart_canvas = FigureCanvasTkAgg(fig, master=self.report_month_bar_container)
                self.report_month_chart_canvas.draw()
                self.report_month_chart_canvas.get_tk_widget().pack(fill="x", expand=True)
            else:
                ctk.CTkLabel(
                    self.report_month_bar_container,
                    text="Chart unavailable (matplotlib missing)",
                    text_color="#8C7D63",
                    font=("Arial", 10, "bold"),
                ).pack(anchor="w")

        if hasattr(self, "report_occupancy_list_container"):
            for widget in self.report_occupancy_list_container.winfo_children():
                widget.destroy()
            filtered_rows = []
            for row in occupancy_rows:
                if self._matches_search(row.get("city"), row.get("occupied_apartments"), row.get("total_apartments")):
                    filtered_rows.append(row)
            for row in filtered_rows[:6]:
                city_name = str(row.get("city", "Unknown"))
                occupied = int(row.get("occupied_apartments", 0) or 0)
                total = int(row.get("total_apartments", 0) or 0)
                pct = int(round(float(row.get("occupancy_rate", 0) or 0)))
                line = ctk.CTkFrame(self.report_occupancy_list_container, fg_color="transparent", corner_radius=0)
                line.pack(fill="x", pady=(2, 8))
                line.grid_columnconfigure(0, weight=0)
                line.grid_columnconfigure(1, weight=1)
                line.grid_columnconfigure(2, weight=0)
                ctk.CTkLabel(line, text=city_name, text_color="#5C4D34", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(line, text=f"{pct}%", text_color="#5C4D34", font=("Arial", 11, "bold")).grid(row=0, column=2, sticky="e", padx=(8, 0))
                progress = ctk.CTkProgressBar(line, height=10, corner_radius=8, progress_color="#C9A84C", fg_color="#E2D9CB")
                progress.grid(row=0, column=1, sticky="ew", padx=10)
                progress.set(max(0.0, min(1.0, pct / 100.0)))
                ctk.CTkLabel(line, text=f"{occupied} / {total} units", text_color="#8C7D63", font=("Arial", 10, "bold")).grid(row=1, column=1, sticky="w", pady=(2, 0))

        if hasattr(self, "report_maintenance_list_container"):
            for widget in self.report_maintenance_list_container.winfo_children():
                widget.destroy()
            category_totals = {
                "Plumbing": 0.0,
                "Electrical": 0.0,
                "Heating / HVAC": 0.0,
                "Structural / Windows": 0.0,
                "General": 0.0,
            }
            for request in maintenance_requests:
                if str(request.get("status", "")).strip().lower() != "resolved":
                    continue
                amount = float(request.get("cost", 0) or 0)
                if amount <= 0:
                    continue
                category = self._categorise_maintenance(request.get("title", ""))
                if not self._matches_search(category, request.get("title", ""), request.get("description", "")):
                    continue
                category_totals[category] += amount

            maintenance_rows = [(k, v) for k, v in category_totals.items() if v > 0]
            if not maintenance_rows:
                maintenance_rows = [("General", total_cost)]
            max_cost = max((row[1] for row in maintenance_rows), default=1.0) or 1.0
            for category, amount in maintenance_rows:
                row_frame = ctk.CTkFrame(self.report_maintenance_list_container, fg_color="transparent", corner_radius=0)
                row_frame.pack(fill="x", pady=(2, 10))
                ctk.CTkLabel(row_frame, text=category, text_color="#5C4D34", font=("Arial", 12, "bold")).pack(side="left")
                ctk.CTkLabel(row_frame, text=f"£{amount:,.0f}", text_color="#2B2418", font=("Arial", 12, "bold")).pack(side="right")
                progress = ctk.CTkProgressBar(row_frame, height=10, corner_radius=8, progress_color="#C9A84C", fg_color="#E2D9CB")
                progress.pack(fill="x", padx=(300, 70), pady=(4, 0))
                progress.set(max(0.0, min(1.0, amount / max_cost)))

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

        self.billing_start_var.set(start_of_month.strftime("%d/%m/%Y"))
        self.billing_end_var.set(end_of_month.strftime("%d/%m/%Y"))

        due_date_value = end_of_month + timedelta(days=7)
        self.invoice_due_var.set(due_date_value.strftime("%d/%m/%Y"))

    # =========================
    # CREATE INVOICE
    # =========================
    def create_invoice(self):
        """
        Generate a new invoice for the selected lease.
        """
        if not AuthController.can_perform_action("process_payments"):
            messagebox.showwarning(
                "Read-only Access",
                "Your role can view financial summaries but cannot create invoices.",
            )
            return

        selected = self.lease_combo.get()
        lease = self.lease_map.get(selected)

        if not lease:
            messagebox.showerror("Error", "Please select a lease.")
            return

        lease_id = lease["leaseID"]
        billing_start_raw = self.billing_start_var.get().strip()
        billing_end_raw = self.billing_end_var.get().strip()
        due_date_raw = self.invoice_due_var.get().strip()
        amount_due_text = self.amount_due_var.get().strip()

        if not billing_start_raw or not billing_end_raw or not due_date_raw or not amount_due_text:
            messagebox.showerror("Error", "Please complete all invoice fields.")
            return

        try:
            billing_start = self._to_storage_date(billing_start_raw)
            billing_end = self._to_storage_date(billing_end_raw)
            due_date_value = self._to_storage_date(due_date_raw)
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

        self._show_success_popup(f"Invoice #{invoice_id} created successfully.")
        self.refresh_all()

    # =========================
    # OPEN INVOICE SELECTION HANDLER
    # =========================
    def _on_invoice_selected_for_payment(self, event=None):
        """
        Auto-fill amount paid with the current outstanding balance.
        """
        if isinstance(event, str):
            selected = event.strip()
        elif hasattr(self, "open_invoice_menu"):
            selected = str(self.open_invoice_menu.get()).strip()
        else:
            selected = ""
        invoice = self.invoice_map.get(selected)

        if not invoice:
            self.amount_paid_var.set("")
            return

        outstanding = InvoiceDAO.get_outstanding_balance(invoice["invoiceID"])
        self.amount_paid_var.set(f"{outstanding:.2f}")

    def _on_city_filter_change(self, selected_value=None):
        if not self.is_admin:
            return
        if isinstance(selected_value, str):
            chosen = selected_value.strip()
        elif hasattr(self, "city_filter_var"):
            chosen = str(self.city_filter_var.get()).strip()
        else:
            chosen = "All Cities"
        self.selected_city = chosen or "All Cities"
        self.city_scope = AuthController.get_city_scope(self.selected_city)
        self.refresh_all()

    # =========================
    # RECORD PAYMENT
    # =========================
    def record_payment(self):
        """
        Record payment for the selected invoice and show a receipt.
        """
        if not AuthController.can_perform_action("process_payments"):
            messagebox.showwarning(
                "Read-only Access",
                "Your role can view financial summaries but cannot process payments.",
            )
            return

        if hasattr(self, "open_invoice_menu"):
            selected = str(self.open_invoice_menu.get()).strip()
        else:
            selected = ""
        invoice = self.invoice_map.get(selected)

        if not invoice:
            messagebox.showerror("Error", "Please select an open invoice.")
            return

        payment_date_input = self.payment_date_var.get().strip()
        amount_paid_text = self.amount_paid_var.get().strip()
        if hasattr(self, "payment_method_menu"):
            payment_method = str(self.payment_method_menu.get()).strip() or "MANUAL"
        else:
            payment_method = "MANUAL"

        try:
            payment_date_value = self._to_storage_date(payment_date_input)
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

        self._show_success_popup(f"Payment #{payment_id} recorded successfully.")
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

        city_scope = self._effective_report_city_scope()
        summary = ReportDAO.get_overall_financial_summary(city=city_scope)
        city_rows = ReportDAO.get_financial_summary_by_city()
        if city_scope:
            city_rows = [row for row in city_rows if str(row.get("city", "")).strip() == city_scope]
        late_rows = ReportDAO.get_late_invoices(city=city_scope)

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

        self._show_success_popup(f"CSV report saved to:\n{path}", title="Export Complete")
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

        city_scope = self._effective_report_city_scope()
        summary = ReportDAO.get_overall_financial_summary(city=city_scope)
        city_rows = ReportDAO.get_financial_summary_by_city()
        if city_scope:
            city_rows = [row for row in city_rows if str(row.get("city", "")).strip() == city_scope]
        late_rows = ReportDAO.get_late_invoices(city=city_scope)

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
        self._show_success_popup(f"PDF report saved to:\n{path}", title="Export Complete")
    
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
        self._show_success_popup(f"Invoice PDF saved to:\n{path}", title="Export Complete")

    def export_selected_payment_pdf(self):
        selected = self.payment_tree.selection()
        payment_id = None
        if selected:
            payment_id = self.payment_tree.item(selected[0], "values")[0]
        elif hasattr(self, "receipt_combo"):
            chosen = self.receipt_combo.get().strip()
            payment_id = self.receipt_map.get(chosen)

        if payment_id is None:
            messagebox.showwarning("No Selection", "Please select a payment first.")
            return

        self._export_payment_pdf_by_id(int(payment_id))

    def _export_payment_pdf_by_id(self, payment_id):
        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror(
                "Missing Package",
                "PDF export needs fpdf2.\n\nInstall it with:\npip install fpdf2"
            )
            return

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
        self._show_success_popup(f"Receipt PDF saved to:\n{path}", title="Export Complete")
