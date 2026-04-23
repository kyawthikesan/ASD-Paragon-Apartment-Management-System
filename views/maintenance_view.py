# Student Name: Kyaw Thike (oliver) San
# Student ID: 25014001
# Module: UFCF8S-30-2 Advanced Software Development

# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import datetime
import customtkinter as ctk

from dao.maintenance_dao import MaintenanceDAO
from dao.user_dao import UserDAO
from controllers.auth_controller import AuthController
from views.premium_shell import PremiumAppShell


class MaintenanceDashboardView(ttk.Frame):
    PAGE_BG = "#F8F5F0"
    CARD_BG = "#FFFFFF"
    BORDER = "#E4D9C9"
    TEXT_MAIN = "#2C2416"
    TEXT_SOFT = "#7E705A"
    GOLD = "#C9A84C"
    GOLD_DEEP = "#9A7A2E"
    SIDEBAR_BG = "#18150F"
    SIDEBAR_PANEL = "#2B2417"
    SIDEBAR_TEXT = "#F2E8D2"
    SIDEBAR_MUTED = "#8F7F63"
    SECTION_TAB_INACTIVE_BG = "#F7F2E8"
    SECTION_TAB_INACTIVE_FG = "#5E5137"
    SECTION_TAB_INACTIVE_BORDER = "#D8CAB0"

    @staticmethod
    def _read_user_value(user, key, default=""):
        if not user:
            return default
        try:
            return user[key]
        except Exception:
            pass
        try:
            return user.get(key, default)
        except Exception:
            return default

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
        super().__init__(parent, style="Maintenance.TFrame")
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
        default_section = "create" if self.current_role in ("front_desk", "admin") else "requests"
        self.active_section = tk.StringVar(value=default_section)

        self.tree = None
        self.request_list_body = None
        self.requests_table_card = None
        self.requests_header_row = None
        self.request_row_card_by_id = {}
        self.request_selected_card_id = None
        self.priority_combo = None
        self.schedule_priority_var = tk.StringVar(value="Medium")
        self.status_filter_var = tk.StringVar(value="All Statuses")
        self._search_query = ""
        self.request_rows_by_id = {}
        self.all_request_rows = []
        self._request_col_weights = (0, 1, 4, 2, 2, 3, 3, 2, 2)

        # Safe shared state across sections
        self.selected_id_var = tk.StringVar(value="None")
        self.assigned_staff_var = tk.StringVar()
        self.scheduled_date_var = tk.StringVar()
        self.scheduled_time_var = tk.StringVar()
        self.hours_spent_var = tk.StringVar(value="0")
        self.cost_var = tk.StringVar(value="0")
        self.resolution_text = None

        # Dashboard summary metrics
        self.summary_open_var = tk.StringVar(value="0")
        self.summary_high_var = tk.StringVar(value="0")
        self.summary_scheduled_var = tk.StringVar(value="0")
        self.summary_cost_var = tk.StringVar(value="£0.00")
        self.summary_open_note_var = tk.StringVar(value="active requests")
        self.summary_high_note_var = tk.StringVar(value="urgent action")
        self.summary_scheduled_note_var = tk.StringVar(value="in progress")
        self.summary_cost_note_var = tk.StringVar(value="resolved tasks")

        self.section_buttons = {}
        self._is_maintenance_role = str(self.current_role or "").strip().lower() == "maintenance"
        shell_logout_action = self.logout_callback if self._is_maintenance_role else (self.home_callback or self.logout_callback)

        self._apply_local_styles()
        self.shell = PremiumAppShell(
            self,
            page_title="Maintenance",
            on_logout=shell_logout_action,
            active_nav="Maintenance",
            nav_sections=self._build_nav_sections(),
            footer_action_label="Logout" if self._is_maintenance_role else ("Back to Dashboard" if self.home_callback else "Logout"),
            search_placeholder="Search maintenance requests...",
            location_label=AuthController.get_current_location(),
            on_search_change=self._on_shell_search,
            on_search_submit=self._on_shell_search,
            on_bell_click=self._show_alerts,
            on_settings_click=self._show_settings,
            notification_count=self._initial_notification_count(),
            hide_sidebar=self._is_maintenance_role,
        )
        self.page_area = self.shell.content

        # Whole-page scroll container for the main content area
        self.canvas = tk.Canvas(self.page_area, highlightthickness=0, bg=self.PAGE_BG)
        # Keep the page scrollable via mouse wheel/trackpad without showing a scrollbar rail.
        self.canvas.configure(yscrollcommand=lambda *_args: None)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content = ttk.Frame(self.canvas, style="Maintenance.TFrame")
        self.content_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind("<Destroy>", self._on_destroy, add="+")

        self._build_ui()
        self.load_data()

    def _build_nav_sections(self):
        role_key = str(self.current_role or "").strip().lower()
        if role_key == "maintenance":
            return [
                {
                    "title": "Management",
                    "items": [
                        {
                            "label": "Maintenance",
                            "action": self.open_maintenance_dashboard,
                            "icon": "maintenance",
                        }
                    ],
                }
            ]

        nav_sections = [
            {
                "title": "Overview",
                "items": [{"label": "Dashboard", "action": self.home_callback, "icon": "dashboard"}],
            },
            {"title": "Management", "items": []},
            {"title": "Finance", "items": []},
            {"title": "Admin", "items": []},
        ]

        if AuthController.can_access_feature("tenant_management", self.current_role):
            nav_sections[1]["items"].append(
                {"label": "Tenants", "action": self.open_tenant_management, "icon": "tenants"}
            )
        if AuthController.can_access_feature("apartment_management", self.current_role):
            nav_sections[1]["items"].append(
                {"label": "Apartments", "action": self.open_apartment_management, "icon": "apartments"}
            )
        if AuthController.can_access_feature("lease_management", self.current_role):
            nav_sections[1]["items"].append(
                {"label": "Leases", "action": self.open_lease_management, "icon": "leases"}
            )
        nav_sections[1]["items"].append(
            {"label": "Maintenance", "action": self.open_maintenance_dashboard, "icon": "maintenance"}
        )

        if AuthController.can_access_feature("finance_dashboard", self.current_role):
            role_key = str(self.current_role or "").strip().lower()
            if role_key == "finance":
                finance_action = self.open_finance_payments or self.open_finance_reports
                nav_sections[2]["items"].append(
                    {"label": "Payments & Reports", "action": finance_action, "icon": "payments"}
                )
            elif role_key == "manager":
                nav_sections[2]["items"].append(
                    {"label": "Reports", "action": self.open_finance_reports, "icon": "reports"}
                )
            else:
                nav_sections[2]["items"].extend(
                    [
                        {"label": "Payments", "action": self.open_finance_payments, "icon": "payments"},
                        {"label": "Reports", "action": self.open_finance_reports, "icon": "reports"},
                    ]
                )

        nav_sections[3]["items"].append(
            {"label": "User Access", "action": self.open_user_management, "icon": "shield"}
        )
        return nav_sections

    def _apply_local_styles(self):
        style = ttk.Style(self)

        style.configure("Maintenance.TFrame", background=self.PAGE_BG)
        style.configure(
            "Maintenance.Title.TLabel",
            background=self.PAGE_BG,
            foreground=self.TEXT_MAIN,
            font=("Georgia", 22, "bold"),
        )
        style.configure(
            "Maintenance.Subtitle.TLabel",
            background=self.PAGE_BG,
            foreground=self.TEXT_SOFT,
            font=("Arial", 11),
        )
        style.configure(
            "Maintenance.TLabel",
            background=self.CARD_BG,
            foreground=self.TEXT_MAIN,
            font=("Arial", 12),
        )

        style.configure(
            "Maintenance.TLabelframe",
            background=self.CARD_BG,
            bordercolor=self.BORDER,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Maintenance.TLabelframe.Label",
            background=self.CARD_BG,
            foreground=self.TEXT_MAIN,
            font=("Arial", 12, "bold"),
        )

        style.configure(
            "Maintenance.Primary.TButton",
            background=self.GOLD,
            foreground="#2C2416",
            padding=(14, 8),
            borderwidth=0,
            font=("Arial", 11, "bold"),
        )
        style.map(
            "Maintenance.Primary.TButton",
            background=[("active", "#B9953F"), ("pressed", "#B9953F")],
        )

        style.configure(
            "Maintenance.Ghost.TButton",
            background="#F2EBDF",
            foreground=self.TEXT_MAIN,
            padding=(14, 8),
            bordercolor="#D8CAB0",
            borderwidth=1,
            font=("Arial", 11),
        )
        style.map(
            "Maintenance.Ghost.TButton",
            background=[("active", "#EBE1D2"), ("pressed", "#E2D6C3")],
        )

        style.configure(
            "Maintenance.Tab.TButton",
            background="#EFE7D8",
            foreground="#5E5137",
            padding=(12, 7),
            borderwidth=1,
            bordercolor="#D8CAB0",
            font=("Arial", 10, "bold"),
        )
        style.map(
            "Maintenance.Tab.TButton",
            background=[("active", "#E4D8C3"), ("pressed", "#DDCFB7")],
        )

        style.configure(
            "Maintenance.TabActive.TButton",
            background=self.GOLD,
            foreground="#2C2416",
            padding=(12, 7),
            borderwidth=0,
            font=("Arial", 10, "bold"),
        )
        style.map(
            "Maintenance.TabActive.TButton",
            background=[("active", "#B9953F"), ("pressed", "#B9953F")],
        )

        style.configure(
            "Maintenance.Treeview",
            background="#FFFFFF",
            foreground=self.TEXT_MAIN,
            rowheight=30,
            fieldbackground="#FFFFFF",
            borderwidth=0,
            font=("Arial", 10),
        )
        style.configure(
            "Maintenance.Treeview.Heading",
            background="#F1EBDD",
            foreground="#8E7D60",
            relief="flat",
            font=("Arial", 10, "bold"),
            padding=(8, 8),
        )
        style.map("Maintenance.Treeview.Heading", background=[("active", "#E9DFC9")])
        style.map(
            "Maintenance.Treeview",
            background=[("selected", "#E9E1D2")],
            foreground=[("selected", self.TEXT_MAIN)],
        )

        style.configure(
            "Maintenance.TEntry",
            fieldbackground="#FFFFFF",
            foreground=self.TEXT_MAIN,
            bordercolor="#DCCEB8",
            lightcolor="#DCCEB8",
            darkcolor="#DCCEB8",
            insertcolor=self.GOLD_DEEP,
            padding=6,
        )
        style.map(
            "Maintenance.TEntry",
            bordercolor=[("focus", self.GOLD_DEEP)],
            lightcolor=[("focus", self.GOLD_DEEP)],
            darkcolor=[("focus", self.GOLD_DEEP)],
        )

        style.configure(
            "Maintenance.TCombobox",
            fieldbackground="#FFFFFF",
            foreground=self.TEXT_MAIN,
            bordercolor="#DCCEB8",
            lightcolor="#DCCEB8",
            darkcolor="#DCCEB8",
            arrowcolor="#8A6A22",
            padding=5,
        )
        style.map(
            "Maintenance.TCombobox",
            bordercolor=[("focus", self.GOLD_DEEP)],
            lightcolor=[("focus", self.GOLD_DEEP)],
            darkcolor=[("focus", self.GOLD_DEEP)],
        )

    def _on_content_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.content_window, width=event.width)

    def _on_mousewheel(self, event):
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        try:
            if not canvas.winfo_exists():
                return
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return
            canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        except tk.TclError:
            # View/canvas was destroyed while global wheel binding still fired.
            self._unbind_mousewheel()

    def _unbind_mousewheel(self):
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass

    def _on_destroy(self, event=None):
        if event is not None and event.widget is not self:
            return
        self._unbind_mousewheel()

    def _build_ui(self):
        self.content.configure(style="Maintenance.TFrame")

        if self._is_maintenance_role:
            self._build_active_jobs_banner()

        self._build_summary_row()

        section_nav = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=0)
        section_nav.pack(fill="x", padx=18, pady=(0, 10))

        if self.current_role in ("front_desk", "admin"):
            self._add_section_button(section_nav, "create", "Create Request")

        if self.current_role in ("front_desk", "maintenance", "admin", "manager"):
            self._add_section_button(section_nav, "requests", "All Requests")

        if self.current_role in ("maintenance",):
            self._add_section_button(section_nav, "schedule", "Schedule / Update")
            self._add_section_button(section_nav, "resolve", "Resolve")

        self.section_container = ttk.Frame(self.content, style="Maintenance.TFrame", padding=(12, 0, 12, 12))
        self.section_container.pack(fill="both", expand=True)

        self.show_section(self.active_section.get())

    def _build_active_jobs_banner(self):
        current_user = AuthController.current_user or {}
        full_name = (
            self._read_user_value(current_user, "full_name")
            or self._read_user_value(current_user, "username")
            or "Maintenance Staff"
        )
        location = AuthController.get_current_location() or "All Cities"
        date_text = datetime.now().strftime("%a %d %b %Y")

        card = ctk.CTkFrame(
            self.content,
            fg_color="#E8EFE6",
            corner_radius=18,
            border_width=1,
            border_color="#A8CFAB",
        )
        card.pack(fill="x", padx=18, pady=(0, 12))
        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(
            card,
            text="🔧",
            text_color="#4C7A52",
            font=("Arial", 28),
            width=56,
            anchor="center",
        ).grid(row=0, column=0, sticky="w", padx=(14, 8), pady=14)

        text_col = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        text_col.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            text_col,
            text=f"{full_name} — Your Active Jobs",
            text_color="#2F6B3F",
            font=("Arial", 18, "bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            text_col,
            text=f"{location} · Maintenance Staff · {date_text}",
            text_color="#4D8A56",
            font=("Arial", 14, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        right_col = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        right_col.grid(row=0, column=2, sticky="e", padx=(8, 20))

        ctk.CTkLabel(
            right_col,
            textvariable=self.summary_open_var,
            text_color="#2F6B3F",
            font=("Georgia", 46, "bold"),
            anchor="e",
        ).pack(anchor="e", pady=(0, 0))
        ctk.CTkLabel(
            right_col,
            text="assigned to you",
            text_color="#4D8A56",
            font=("Arial", 15),
            anchor="e",
        ).pack(anchor="e")

    def _build_summary_row(self):
        row = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=0)
        row.pack(fill="x", padx=18, pady=(0, 10))

        for i in range(4):
            row.grid_columnconfigure(i, weight=1)

        role_key = str(self.current_role or "").strip().lower()
        if role_key == "maintenance":
            cards = [
                ("MY OPEN JOBS", self.summary_open_var, self.summary_open_note_var, self.TEXT_MAIN),
                ("HIGH PRIORITY", self.summary_high_var, self.summary_high_note_var, "#8A2A2A"),
                ("SCHEDULED TODAY", self.summary_scheduled_var, self.summary_scheduled_note_var, "#7A5A0A"),
                ("MY YTD COST", self.summary_cost_var, self.summary_cost_note_var, self.TEXT_MAIN),
            ]
        else:
            cards = [
                ("TOTAL OPEN", self.summary_open_var, self.summary_open_note_var, self.TEXT_MAIN),
                ("HIGH PRIORITY", self.summary_high_var, self.summary_high_note_var, "#8A2A2A"),
                ("SCHEDULED", self.summary_scheduled_var, self.summary_scheduled_note_var, "#7A5A0A"),
                ("YTD COST", self.summary_cost_var, self.summary_cost_note_var, self.TEXT_MAIN),
            ]

        for idx, (title, value_var, note_var, value_color) in enumerate(cards):
            card = ctk.CTkFrame(
                row,
                fg_color=self.CARD_BG,
                corner_radius=10,          # smaller corners
                border_width=1,
                border_color=self.BORDER,
                height=108                # fixed smaller height
            )
            card.grid(
                row=0,
                column=idx,
                sticky="nsew",
                padx=(0, 8) if idx < len(cards) - 1 else 0
            )
            card.grid_propagate(False)     # keep compact fixed height

            ctk.CTkLabel(
                card,
                text=title,
                text_color="#9A8A70",
                font=("Arial", 11, "bold"),
                anchor="w",
            ).pack(anchor="w", padx=16, pady=(12, 0))

            ctk.CTkLabel(
                card,
                textvariable=value_var,
                text_color=value_color,
                font=("Georgia", 24, "bold"),
                anchor="w",
            ).pack(anchor="w", padx=16, pady=(4, 0))

            ctk.CTkLabel(
                card,
                textvariable=note_var,
                text_color="#8E7E67",
                font=("Arial", 10),
                anchor="w",
            ).pack(anchor="w", padx=16, pady=(0, 12))

    def _add_section_button(self, parent, key, label):
        btn = ctk.CTkButton(
            parent,
            text=label,
            command=lambda section=key: self.show_section(section),
            fg_color=self.SECTION_TAB_INACTIVE_BG,
            hover_color="#E4D8C3",
            text_color=self.SECTION_TAB_INACTIVE_FG,
            corner_radius=14,
            border_width=1,
            border_color=self.SECTION_TAB_INACTIVE_BORDER,
            width=126,
            height=36,
            font=("Arial", 12, "bold"),
        )
        btn.pack(side="left", padx=(0, 8))
        self.section_buttons[key] = btn

    def _add_panel_accent(self, parent):
        accent = tk.Frame(parent, bg=self.GOLD, height=3, bd=0, highlightthickness=0)
        accent.pack(fill="x", side="top")

    def _refresh_section_tabs(self):
        for key, button in self.section_buttons.items():
            is_active = key == self.active_section.get()
            button.configure(
                fg_color=self.GOLD if is_active else self.SECTION_TAB_INACTIVE_BG,
                hover_color="#B9953F" if is_active else "#E4D8C3",
                text_color="#2C2416" if is_active else self.SECTION_TAB_INACTIVE_FG,
                border_width=0 if is_active else 1,
                border_color=self.GOLD if is_active else self.SECTION_TAB_INACTIVE_BORDER,
            )

    def _safe_float(self, value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _refresh_summary_cards(self, rows):
        open_count = 0
        high_count = 0
        scheduled_count = 0
        total_cost = 0.0

        for row in rows:
            status = str(row.get("status", "")).strip().lower()
            priority = str(row.get("priority", "")).strip().lower()
            cost = self._safe_float(row.get("cost", 0))

            total_cost += cost

            if status not in {"resolved", "closed"}:
                open_count += 1

            if priority in {"high", "urgent"} and status not in {"resolved", "closed"}:
                high_count += 1

            if status in {"scheduled", "in progress", "in_progress"}:
                scheduled_count += 1

        self.summary_open_var.set(str(open_count))
        self.summary_high_var.set(str(high_count))
        self.summary_scheduled_var.set(str(scheduled_count))
        self.summary_cost_var.set(f"£{total_cost:,.2f}")
        role_key = str(self.current_role or "").strip().lower()
        if role_key == "maintenance":
            self.summary_open_note_var.set("assigned to you")
            self.summary_high_note_var.set("need action today")
            self.summary_scheduled_note_var.set("upcoming")
            self.summary_cost_note_var.set("resolved by you")
        else:
            self.summary_open_note_var.set("active requests")
            self.summary_high_note_var.set("urgent action")
            self.summary_scheduled_note_var.set("in progress")
            self.summary_cost_note_var.set("resolved tasks")

    def show_section(self, section_name):
        role = str(self.current_role or "").strip().lower()
        if section_name == "create" and role not in ("front_desk", "admin"):
            return
        if section_name == "schedule" and role not in ("maintenance",):
            return
        if section_name == "resolve" and role != "maintenance":
            return

        self.active_section.set(section_name)
        self._refresh_section_tabs()

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

        create_frame = ctk.CTkFrame(
            parent,
            fg_color=self.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        create_frame.pack(fill="x", pady=(0, 10))

        header = ctk.CTkFrame(create_frame, fg_color="transparent", corner_radius=0)
        header.pack(fill="x", padx=18, pady=(14, 10))

        ctk.CTkLabel(
            header,
            text="Create Maintenance Request",
            text_color=self.TEXT_MAIN,
            font=("Arial", 17, "bold"),
        ).pack(side="left")

        divider = ctk.CTkFrame(create_frame, fg_color="#ECE1CD", corner_radius=0, height=1)
        divider.pack(fill="x")

        form_wrap = ctk.CTkFrame(create_frame, fg_color="transparent", corner_radius=0)
        form_wrap.pack(fill="x", padx=18, pady=(14, 14))

        self.create_form = ctk.CTkFrame(form_wrap, fg_color="transparent", corner_radius=0)
        self.create_form.pack(fill="x")

        self.tenant_options = self.dao.get_tenant_options()
        tenant_labels = [item["label"] for item in self.tenant_options]
        tenant_values = ["Select tenant..."] + tenant_labels

        self.create_tenant_var = tk.StringVar(value="Select tenant...")
        self.create_apartment_id_var = tk.StringVar(value="Auto-populated")
        self.create_title_var = tk.StringVar()
        self.create_priority_var = tk.StringVar(value="Medium")

        def build_label(parent_widget, text):
            return ctk.CTkLabel(
                parent_widget,
                text=text,
                text_color="#9A8A70",
                font=("Arial", 10, "bold"),
                anchor="w",
            )

        self.tenant_label = build_label(self.create_form, "TENANT")
        self.tenant_dropdown = ctk.CTkComboBox(
            self.create_form,
            variable=self.create_tenant_var,
            values=tenant_values,
            command=lambda _value: self.auto_fill_apartment_from_tenant(),
            state="readonly",
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            button_color="#E4D8C3",
            button_hover_color="#D8CAB0",
            text_color=self.TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=self.TEXT_MAIN,
            dropdown_hover_color="#F3ECDD",
            corner_radius=10,
            height=40,
            font=("Arial", 13),
        )

        self.apartment_label = build_label(self.create_form, "APARTMENT ID")
        self.apt_entry = ctk.CTkEntry(
            self.create_form,
            textvariable=self.create_apartment_id_var,
            state="disabled",
            fg_color="#EDE8DC",
            border_color="#DCCEB8",
            border_width=1,
            text_color="#6B5D44",
            corner_radius=10,
            height=40,
            font=("Arial", 13, "bold"),
        )

        self.title_label = build_label(self.create_form, "REQUEST TITLE")
        self.title_entry = ctk.CTkEntry(
            self.create_form,
            textvariable=self.create_title_var,
            placeholder_text="e.g. Boiler not heating — Unit D-108",
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            text_color=self.TEXT_MAIN,
            placeholder_text_color="#8F8576",
            corner_radius=10,
            height=40,
            font=("Arial", 13),
        )

        self.desc_label = build_label(self.create_form, "DESCRIPTION")
        self.create_description_text = ctk.CTkTextbox(
            self.create_form,
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            text_color=self.TEXT_MAIN,
            corner_radius=10,
            height=96,
            font=("Arial", 13),
            wrap="word",
        )

        self._create_desc_placeholder = (
            "Describe the issue — what was reported, when it started, any safety concerns..."
        )
        self._set_textbox_placeholder(self.create_description_text, self._create_desc_placeholder)
        self.create_description_text.bind(
            "<FocusIn>",
            lambda e: self._clear_textbox_placeholder(
                self.create_description_text, self._create_desc_placeholder
            ),
        )
        self.create_description_text.bind(
            "<FocusOut>",
            lambda e: self._restore_textbox_placeholder(
                self.create_description_text, self._create_desc_placeholder
            ),
        )

        self.priority_label = build_label(self.create_form, "PRIORITY")
        self.create_priority_combo = ctk.CTkComboBox(
            self.create_form,
            variable=self.create_priority_var,
            values=["Low", "Medium", "High", "Urgent"],
            state="readonly",
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            button_color="#E4D8C3",
            button_hover_color="#D8CAB0",
            text_color=self.TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=self.TEXT_MAIN,
            dropdown_hover_color="#F3ECDD",
            corner_radius=10,
            height=40,
            font=("Arial", 13),
        )

        self.create_button = ctk.CTkButton(
            self.create_form,
            text="Create Request",
            command=self.create_request,
            fg_color="#F8F5F0",
            hover_color="#EEE4D2",
            text_color="#1E1B15",
            border_width=1,
            border_color="#BFB5A5",
            corner_radius=12,
            height=40,
            font=("Arial", 13, "bold"),
        )

        self.note = ctk.CTkFrame(
            self.create_form,
            fg_color="#F5F0E6",
            border_width=1,
            border_color="#E1D2B7",
            corner_radius=12,
        )
        self.note_label = ctk.CTkLabel(
            self.note,
            text="Note: New requests start as Open. Maintenance staff will schedule and resolve them.",
            text_color="#6B5D44",
            font=("Arial", 11, "bold"),
            justify="left",
            anchor="w",
        )
        self.note_label.pack(fill="x", padx=12, pady=10)

        self._layout_create_form()
        self.create_frame = create_frame
        self.create_frame.bind("<Configure>", lambda e: self._layout_create_form(), add="+")

    def _layout_create_form(self):
        if not hasattr(self, "create_form") or not self.create_form.winfo_exists():
            return

        for widget in self.create_form.winfo_children():
            widget.grid_forget()

        width = self.create_form.winfo_width()
        compact = width < 760

        for i in range(2):
            self.create_form.grid_columnconfigure(i, weight=0)
        self.create_form.grid_columnconfigure(0, weight=1)
        if not compact:
            self.create_form.grid_columnconfigure(1, weight=1)

        pad_x_left = (2, 10)
        pad_x_right = (10, 2)

        if compact:
            self.tenant_label.grid(row=0, column=0, sticky="w", padx=2, pady=(0, 4))
            self.tenant_dropdown.grid(row=1, column=0, sticky="ew", padx=2, pady=(0, 10))

            self.apartment_label.grid(row=2, column=0, sticky="w", padx=2, pady=(0, 4))
            self.apt_entry.grid(row=3, column=0, sticky="ew", padx=2, pady=(0, 10))

            self.title_label.grid(row=4, column=0, sticky="w", padx=2, pady=(0, 4))
            self.title_entry.grid(row=5, column=0, sticky="ew", padx=2, pady=(0, 10))

            self.desc_label.grid(row=6, column=0, sticky="w", padx=2, pady=(0, 4))
            self.create_description_text.grid(row=7, column=0, sticky="ew", padx=2, pady=(0, 10))

            self.priority_label.grid(row=8, column=0, sticky="w", padx=2, pady=(0, 4))
            self.create_priority_combo.grid(row=9, column=0, sticky="ew", padx=2, pady=(0, 10))

            self.create_button.grid(row=10, column=0, sticky="ew", padx=2, pady=(2, 10))

            self.note.grid(row=11, column=0, sticky="ew", padx=2, pady=(0, 2))

        else:
            self.tenant_label.grid(row=0, column=0, sticky="w", padx=pad_x_left, pady=(0, 4))
            self.apartment_label.grid(row=0, column=1, sticky="w", padx=pad_x_right, pady=(0, 4))

            self.tenant_dropdown.grid(row=1, column=0, sticky="ew", padx=pad_x_left, pady=(0, 10))
            self.apt_entry.grid(row=1, column=1, sticky="ew", padx=pad_x_right, pady=(0, 10))

            self.title_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=2, pady=(0, 4))
            self.title_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=2, pady=(0, 10))

            self.desc_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=2, pady=(0, 4))
            self.create_description_text.grid(row=5, column=0, columnspan=2, sticky="ew", padx=2, pady=(0, 10))

            self.priority_label.grid(row=6, column=0, sticky="w", padx=pad_x_left, pady=(0, 4))
            self.priority_combo = self.create_priority_combo
            self.create_priority_combo.grid(row=7, column=0, sticky="ew", padx=pad_x_left, pady=(0, 10))

            self.create_button.grid(row=7, column=1, sticky="e", padx=pad_x_right, pady=(0, 10))

            self.note.grid(row=8, column=0, columnspan=2, sticky="ew", padx=2, pady=(0, 2))

    def _set_textbox_placeholder(self, textbox, placeholder):
        textbox.delete("1.0", tk.END)
        textbox.insert("1.0", placeholder)
        textbox.configure(text_color="#8F8576")
        textbox._placeholder_active = True


    def _clear_textbox_placeholder(self, textbox, placeholder):
        current_text = textbox.get("1.0", tk.END).strip()
        if current_text == placeholder and getattr(textbox, "_placeholder_active", False):
            textbox.delete("1.0", tk.END)
            textbox.configure(text_color=self.TEXT_MAIN)
            textbox._placeholder_active = False


    def _restore_textbox_placeholder(self, textbox, placeholder):
        current_text = textbox.get("1.0", tk.END).strip()
        if not current_text:
            self._set_textbox_placeholder(textbox, placeholder)

    def _build_requests_section(self, parent):
        outer = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        outer.pack(fill="both", expand=True)

        table_card = ctk.CTkFrame(
            outer,
            fg_color=self.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        table_card.pack(fill="both", expand=True)
        self.requests_table_card = table_card

        # Header area
        header_wrap = ctk.CTkFrame(table_card, fg_color="transparent", corner_radius=0, height=78)
        header_wrap.pack(fill="x", padx=0, pady=0)
        header_wrap.pack_propagate(False)

        title_wrap = ctk.CTkFrame(header_wrap, fg_color="transparent", corner_radius=0)
        title_wrap.pack(side="left", fill="y", padx=(20, 8), pady=14)

        ctk.CTkLabel(
            title_wrap,
            text="All Maintenance Requests",
            text_color=self.TEXT_MAIN,
            font=("Arial", 16, "bold"),
        ).pack(anchor="w", pady=(6, 0))

        controls_wrap = ctk.CTkFrame(header_wrap, fg_color="transparent", corner_radius=0)
        controls_wrap.pack(side="right", padx=(10, 18), pady=14)

        filter_values = ["All Statuses", "Open", "Scheduled", "In Progress", "Resolved"]
        self.status_filter_var.set(self.status_filter_var.get() or "All Statuses")

        self.status_filter_menu = ctk.CTkComboBox(
            controls_wrap,
            variable=self.status_filter_var,
            values=filter_values,
            command=lambda _choice: self.apply_request_filter(),
            state="readonly",
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            button_color="#EEE5D7",
            button_hover_color="#F5EFE4",
            text_color=self.TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=self.TEXT_MAIN,
            dropdown_hover_color="#F3ECDD",
            corner_radius=12,
            width=208,
            height=42,
            font=("Arial", 12),
            justify="left",
        )
        self.status_filter_menu.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            controls_wrap,
            text="Export CSV",
            command=self.export_requests_csv,
            fg_color="transparent",
            hover_color="#F5EFE4",
            text_color="#B2861B",
            corner_radius=12,
            width=102,
            height=44,
            font=("Arial", 12, "bold"),
        ).pack(side="left")

        divider = ctk.CTkFrame(table_card, fg_color="#EFE6D7", corner_radius=0, height=1)
        divider.pack(fill="x")

        # Header labels aligned to the same content width as row cards.
        header_row = ctk.CTkFrame(table_card, fg_color="transparent", corner_radius=0, height=40)
        header_row.pack(fill="x", padx=12, pady=(2, 0))
        header_row.pack_propagate(False)
        self.requests_header_row = header_row

        header_columns = [
            ("", 0, "w"),
            ("ID", 1, "w"),
            ("TITLE", 4, "w"),
            ("PRIORITY", 2, "w"),
            ("STATUS", 2, "w"),
            ("ASSIGNED STAFF", 3, "w"),
            ("SCHEDULED", 3, "w"),
            ("COST", 1, "center"),
            ("HOURS", 1, "center"),
        ]
        for idx, (_, weight, _anchor) in enumerate(header_columns):
            header_row.grid_columnconfigure(idx, weight=weight)

        for col_idx, (label, _weight, anchor) in enumerate(header_columns):
            if col_idx == 0:
                continue
            if col_idx in (3, 4, 7, 8):
                column_anchor = "center"
                column_padx = (0, 0)
            elif col_idx in (1, 2, 5, 6):
                column_anchor = "w"
                column_padx = (0, 6)
            else:
                column_anchor = anchor
                column_padx = (0, 6)
            ctk.CTkLabel(
                header_row,
                text=label,
                text_color="#9A8A70",
                font=("Arial", 11, "bold"),
                anchor=column_anchor,
            ).grid(row=0, column=col_idx, sticky="nsew", padx=column_padx, pady=12)

        ctk.CTkFrame(table_card, fg_color="#EFE6D7", corner_radius=0, height=1).pack(fill="x")

        # CustomTkinter rounded rows
        list_wrap = ctk.CTkFrame(table_card, fg_color="transparent", corner_radius=0)
        list_wrap.pack(fill="both", expand=True, padx=8, pady=8)

        self.request_list_body = ctk.CTkFrame(
            list_wrap,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        self.request_list_body.pack(fill="both", expand=True)
        self.tree = None
        self._apply_request_column_layout()
        table_card.bind("<Configure>", lambda _e: self._apply_request_column_layout(), add="+")

        self.load_data()

    def _get_priority_colors(self, priority):
        value = str(priority or "").strip().lower()
        if value == "urgent":
            return "#7D1010", "#D44336"
        if value == "high":
            return "#9C2F2F", "#E27A35"
        if value == "medium":
            return "#7A5A0A", "#C7A13A"
        if value == "low":
            return "#397C43", "#4F8D53"
        return self.TEXT_MAIN, "#BCA98A"

    def _get_status_pill_colors(self, status):
        value = str(status or "").strip().lower()
        if value == "open":
            return "#DEE9F6", "#20558A"
        if value in ("in progress", "in_progress"):
            return "#E7E2D7", "#65593E"
        if value == "scheduled":
            return "#F2E6CD", "#7C5B09"
        if value == "resolved":
            return "#DDEADE", "#3D7444"
        return "#EEE8DD", "#6B5D44"

    def _get_row_bg_color(self, row):
        return "#F8F7F4"

    def _bind_click_recursive(self, widget, handler):
        widget.bind("<Button-1>", handler)
        for child in widget.winfo_children():
            self._bind_click_recursive(child, handler)

    def _compute_request_column_minsizes(self):
        if self.request_list_body is not None and self.request_list_body.winfo_exists():
            total_width = int(self.request_list_body.winfo_width())
        elif self.requests_header_row is not None and self.requests_header_row.winfo_exists():
            total_width = int(self.requests_header_row.winfo_width())
        else:
            return None
        if total_width <= 0:
            return None

        weights = self._request_col_weights
        total_weight = sum(weights) or 1
        minsizes = [int(total_width * weight / total_weight) for weight in weights]
        # Fixed left lane reserved for the vertical priority accent.
        minsizes[0] = 22

        # Keep right-side columns readable so COST/HOURS headers are never clipped.
        desired_min = {
            7: 96,   # COST
            8: 102,  # HOURS
        }
        for col, target in desired_min.items():
            if minsizes[col] < target:
                deficit = target - minsizes[col]
                minsizes[col] = target
                # Borrow width from broader columns first.
                for donor in (2, 6, 5):
                    if deficit <= 0:
                        break
                    available = max(0, minsizes[donor] - 120)
                    take = min(available, deficit)
                    minsizes[donor] -= take
                    deficit -= take

        remainder = total_width - sum(minsizes)
        if remainder > 0:
            minsizes[2] += remainder
        return minsizes

    def _apply_request_column_layout(self, row_card=None):
        minsizes = self._compute_request_column_minsizes()
        if minsizes is None:
            return

        if self.requests_header_row is not None and self.requests_header_row.winfo_exists():
            for col, weight in enumerate(self._request_col_weights):
                self.requests_header_row.grid_columnconfigure(col, weight=weight, minsize=minsizes[col])

        if row_card is not None:
            if row_card.winfo_exists():
                for col, weight in enumerate(self._request_col_weights):
                    row_card.grid_columnconfigure(col, weight=weight, minsize=minsizes[col])
            return

        for existing_row in self.request_row_card_by_id.values():
            if not existing_row.winfo_exists():
                continue
            for col, weight in enumerate(self._request_col_weights):
                existing_row.grid_columnconfigure(col, weight=weight, minsize=minsizes[col])

    def _set_selected_request_card(self, request_id):
        previous_id = self.request_selected_card_id
        if previous_id is not None and previous_id in self.request_row_card_by_id:
            prev_card = self.request_row_card_by_id[previous_id]
            if prev_card.winfo_exists():
                prev_card.configure(border_width=1, border_color="#E6DAC6")

        self.request_selected_card_id = request_id
        if request_id in self.request_row_card_by_id:
            selected_card = self.request_row_card_by_id[request_id]
            if selected_card.winfo_exists():
                selected_card.configure(border_width=2, border_color="#C9A84C")

    def _populate_request_cards(self, rows):
        if self.request_list_body is None or not self.request_list_body.winfo_exists():
            return

        for child in self.request_list_body.winfo_children():
            child.destroy()

        self.request_row_card_by_id = {}

        if not rows:
            ctk.CTkLabel(
                self.request_list_body,
                text="No maintenance requests found.",
                text_color="#8F816B",
                font=("Arial", 12),
            ).pack(anchor="w", padx=10, pady=12)
            self.selected_request_id = None
            self.selected_id_var.set("None")
            self.request_selected_card_id = None
            return

        for row in rows:
            scheduled_date = str(row.get("scheduled_date", "") or "").strip()
            scheduled_time = str(row.get("scheduled_time", "") or "").strip()
            if scheduled_date and scheduled_time:
                scheduled_display = f"{scheduled_date} {scheduled_time}"
            elif scheduled_date:
                scheduled_display = scheduled_date
            elif scheduled_time:
                scheduled_display = scheduled_time
            else:
                scheduled_display = "-"

            cost_value = self._safe_float(row.get("cost", 0))
            hours_value = self._safe_float(row.get("hours_spent", 0))
            priority_display = self._format_priority_display(row.get("priority", ""))
            status_display = self._format_status_display(row.get("status", ""))
            priority_text_color, accent_color = self._get_priority_colors(priority_display)
            status_bg, status_fg = self._get_status_pill_colors(status_display)

            request_id_raw = str(row.get("requestID", "")).strip()
            if request_id_raw and request_id_raw != "None":
                display_id = f"MNT-{int(request_id_raw):04d}"
            else:
                display_id = "-"

            row_card = ctk.CTkFrame(
                self.request_list_body,
                fg_color=self._get_row_bg_color(row),
                corner_radius=14,
                border_width=1,
                border_color="#E6DAC6",
                height=56,
            )
            row_card.pack(fill="x", padx=4, pady=(0, 8))
            row_card.pack_propagate(False)

            for idx, weight in enumerate(self._request_col_weights):
                row_card.grid_columnconfigure(idx, weight=weight)

            ctk.CTkFrame(
                row_card,
                fg_color=accent_color,
                corner_radius=6,
                width=6,
                height=30,
            ).grid(row=0, column=0, padx=(8, 8), pady=12, sticky="ns")

            ctk.CTkLabel(row_card, text=display_id, text_color="#9A8A70", font=("Arial", 11, "bold"), anchor="w").grid(
                row=0, column=1, sticky="ew", padx=(0, 6), pady=10
            )
            ctk.CTkLabel(
                row_card,
                text=row.get("title", "") or "-",
                text_color=self.TEXT_MAIN,
                font=("Arial", 11, "bold"),
                anchor="w",
            ).grid(row=0, column=2, sticky="ew", padx=(0, 6), pady=10)
            ctk.CTkLabel(
                row_card,
                text=priority_display,
                text_color=priority_text_color,
                font=("Arial", 11, "bold"),
                anchor="center",
            ).grid(row=0, column=3, sticky="n", pady=10)

            ctk.CTkLabel(
                row_card,
                text=status_display,
                fg_color=status_bg,
                text_color=status_fg,
                corner_radius=999,
                font=("Arial", 11, "bold"),
                width=106,
                height=26,
                anchor="center",
            ).grid(row=0, column=4, pady=10)

            ctk.CTkLabel(
                row_card, text=row.get("assigned_staff", "") or "-", text_color="#6B5D44", font=("Arial", 11), anchor="w"
            ).grid(row=0, column=5, sticky="ew", padx=(0, 6), pady=10)
            ctk.CTkLabel(
                row_card, text=scheduled_display, text_color="#6B5D44", font=("Arial", 11), anchor="w"
            ).grid(row=0, column=6, sticky="ew", padx=(0, 6), pady=10)
            ctk.CTkLabel(
                row_card,
                text=f"£{cost_value:,.2f}" if cost_value > 0 else "-",
                text_color="#8A9A88" if status_display == "Resolved" else "#6B5D44",
                font=("Arial", 11, "bold"),
                anchor="center",
            ).grid(row=0, column=7, sticky="n", pady=10)
            ctk.CTkLabel(
                row_card,
                text=f"{hours_value:.1f}" if hours_value > 0 else "-",
                text_color="#8A9A88" if status_display == "Resolved" else "#6B5D44",
                font=("Arial", 11, "bold"),
                anchor="center",
            ).grid(row=0, column=8, sticky="n", pady=10)

            def on_row_click(_event, rid=request_id_raw, did=display_id):
                self.on_select_request(request_id=rid, display_id=did)

            self._bind_click_recursive(row_card, on_row_click)
            self.request_row_card_by_id[request_id_raw] = row_card
            self._apply_request_column_layout(row_card)

        self.selected_request_id = None
        self.selected_id_var.set("None")
        self.request_selected_card_id = None

    def open_schedule_for_selected(self):
        if not self.selected_request_id:
            messagebox.showwarning("No Request Selected", "Please select a request from Maintenance Req first.")
            return

        self.show_section("schedule")

    def open_resolve_for_selected(self):
        if not self.selected_request_id:
            messagebox.showwarning("No Request Selected", "Please select a request from Maintenance Req first.")
            return

        self.show_section("resolve")

    def _build_schedule_section(self, parent):
        if self.current_role not in ("maintenance",):
            return
        root = self.winfo_toplevel()
        root.update_idletasks()
        compact_ui = int(root.winfo_height() or 0) < 980
        field_height = 34 if compact_ui else 40
        title_font_size = 15 if compact_ui else 17
        role_font_size = 12 if compact_ui else 14
        meta_font_size = 9 if compact_ui else 10
        value_font_size = 12 if compact_ui else 14
        card_pad = 12 if compact_ui else 16
        top_pad = 10 if compact_ui else 14

        wrap = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        wrap.pack(fill="both", expand=True)

        alert_card = ctk.CTkFrame(
            wrap,
            fg_color="#F5ECD5",
            corner_radius=14,
            border_width=1,
            border_color="#E2CF9F",
        )
        alert_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            alert_card,
            text="No request selected. Go to All Requests, click a row, then return here."
            if not self.selected_request_id
            else f"Editing {self.selected_id_var.get()}",
            text_color="#7A5A0A",
            font=("Arial", 12 if compact_ui else 13, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=10 if compact_ui else 12)

        body = ctk.CTkFrame(wrap, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=11)
        body.grid_columnconfigure(1, weight=10)
        body.grid_rowconfigure(0, weight=0)
        body.grid_rowconfigure(1, weight=0)

        left_card = ctk.CTkFrame(
            body,
            fg_color=self.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_card.grid_columnconfigure(0, weight=1)
        left_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            left_card,
            text="Schedule / Update Request",
            text_color=self.TEXT_MAIN,
            font=("Arial", title_font_size, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=card_pad, pady=(top_pad, 6 if compact_ui else 8))
        ctk.CTkLabel(
            left_card,
            text="Maintenance Staff",
            text_color="#4D8A56",
            font=("Arial", role_font_size),
            anchor="e",
        ).grid(row=0, column=1, sticky="e", padx=card_pad, pady=(top_pad, 6 if compact_ui else 8))

        divider = ctk.CTkFrame(left_card, fg_color="#ECE1CD", corner_radius=0, height=1)
        divider.grid(row=1, column=0, columnspan=2, sticky="ew")

        form = ctk.CTkFrame(left_card, fg_color="transparent", corner_radius=0)
        form.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=card_pad, pady=(10 if compact_ui else 12, 10 if compact_ui else 14))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            form,
            text="SELECTED REQUEST ID",
            text_color="#9A8A70",
            font=("Arial", meta_font_size, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        ctk.CTkLabel(
            form,
            text=self.selected_id_var.get(),
            text_color=self.TEXT_MAIN,
            font=("Arial", value_font_size, "bold"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(0, 8 if compact_ui else 10))

        ctk.CTkLabel(
            form,
            text="ASSIGNED STAFF MEMBER",
            text_color="#9A8A70",
            font=("Arial", meta_font_size, "bold"),
            anchor="w",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ctk.CTkEntry(
            form,
            textvariable=self.assigned_staff_var,
            placeholder_text="Your name or colleague",
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            text_color=self.TEXT_MAIN,
            corner_radius=10,
            height=field_height,
            font=("Arial", 13),
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8 if compact_ui else 10))

        ctk.CTkLabel(
            form,
            text="SCHEDULED DATE",
            text_color="#9A8A70",
            font=("Arial", meta_font_size, "bold"),
            anchor="w",
        ).grid(row=4, column=0, sticky="w", pady=(0, 4))
        ctk.CTkLabel(
            form,
            text="SCHEDULED TIME",
            text_color="#9A8A70",
            font=("Arial", meta_font_size, "bold"),
            anchor="w",
        ).grid(row=4, column=1, sticky="w", padx=(10, 0), pady=(0, 4))

        date_row = ctk.CTkFrame(form, fg_color="transparent", corner_radius=0)
        date_row.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        date_row.grid_columnconfigure(0, weight=1)

        self._date_validate_cmd = (self.register(self._validate_iso_date_input), "%P")
        ctk.CTkEntry(
            date_row,
            textvariable=self.scheduled_date_var,
            placeholder_text="YYYY-MM-DD",
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            text_color=self.TEXT_MAIN,
            corner_radius=10,
            height=field_height,
            font=("Arial", 13),
            validate="key",
            validatecommand=self._date_validate_cmd,
        ).grid(row=0, column=0, sticky="ew")

        time_values = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in (0, 15, 30, 45)]
        self.time_combo = ctk.CTkComboBox(
            form,
            variable=self.scheduled_time_var,
            values=time_values,
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            button_color="#E4D8C3",
            button_hover_color="#D8CAB0",
            text_color=self.TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=self.TEXT_MAIN,
            dropdown_hover_color="#F3ECDD",
            corner_radius=10,
            height=field_height,
            font=("Arial", 13),
            state="readonly",
        )
        self.time_combo.grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=(0, 8 if compact_ui else 10))

        if not self.scheduled_time_var.get().strip():
            self.scheduled_time_var.set("09:00")

        ctk.CTkLabel(
            form,
            text="UPDATE PRIORITY",
            text_color="#9A8A70",
            font=("Arial", meta_font_size, "bold"),
            anchor="w",
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.priority_combo = ctk.CTkComboBox(
            form,
            variable=self.schedule_priority_var,
            values=["Low", "Medium", "High", "Urgent"],
            state="readonly",
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            button_color="#E4D8C3",
            button_hover_color="#D8CAB0",
            text_color=self.TEXT_MAIN,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=self.TEXT_MAIN,
            dropdown_hover_color="#F3ECDD",
            corner_radius=10,
            height=field_height,
            font=("Arial", 13),
        )
        self.priority_combo.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 10 if compact_ui else 14))
        self.priority_combo.set(self.schedule_priority_var.get() or "Medium")

        actions = ctk.CTkFrame(form, fg_color="transparent", corner_radius=0)
        actions.grid(row=8, column=0, columnspan=2, sticky="w")

        ctk.CTkButton(
            actions,
            text="Save Schedule",
            command=self.schedule_selected_request,
            fg_color="#F8F5F0",
            hover_color="#EEE4D2",
            text_color="#1E1B15",
            border_width=1,
            border_color="#BFB5A5",
            corner_radius=12,
            height=36 if compact_ui else 40,
            width=146 if compact_ui else 162,
            font=("Arial", 12 if compact_ui else 13, "bold"),
        ).pack(side="left", padx=(0, 8 if compact_ui else 10))

        ctk.CTkButton(
            actions,
            text="Back",
            command=lambda: self.show_section("requests"),
            fg_color="#F8F5F0",
            hover_color="#EEE4D2",
            text_color="#1E1B15",
            border_width=1,
            border_color="#BFB5A5",
            corner_radius=12,
            height=36 if compact_ui else 40,
            width=100 if compact_ui else 110,
            font=("Arial", 12 if compact_ui else 13, "bold"),
        ).pack(side="left")

        right_col = ctk.CTkFrame(body, fg_color="transparent", corner_radius=0)
        right_col.grid(row=0, column=1, sticky="nsew")

        timeline_card = ctk.CTkFrame(
            right_col,
            fg_color=self.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        timeline_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            timeline_card,
            text="Request Timeline",
            text_color=self.TEXT_MAIN,
            font=("Arial", 14 if compact_ui else 16, "bold"),
            anchor="w",
        ).pack(fill="x", padx=card_pad, pady=(top_pad, 6 if compact_ui else 8))
        ctk.CTkFrame(timeline_card, fg_color="#ECE1CD", corner_radius=0, height=1).pack(fill="x")
        ctk.CTkLabel(
            timeline_card,
            text=self._schedule_timeline_text(),
            text_color="#8E7E67",
            font=("Arial", 11 if compact_ui else 12),
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=card_pad, pady=10 if compact_ui else 14)

        staff_card = ctk.CTkFrame(
            right_col,
            fg_color=self.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        staff_card.pack(fill="both", expand=True)
        ctk.CTkLabel(
            staff_card,
            text="Staff Availability",
            text_color=self.TEXT_MAIN,
            font=("Arial", 14 if compact_ui else 16, "bold"),
            anchor="w",
        ).pack(fill="x", padx=card_pad, pady=(top_pad, 6 if compact_ui else 8))
        ctk.CTkFrame(staff_card, fg_color="#ECE1CD", corner_radius=0, height=1).pack(fill="x")

        staff_list = ctk.CTkFrame(staff_card, fg_color="transparent", corner_radius=0)
        staff_list.pack(fill="x", expand=False, padx=card_pad, pady=8 if compact_ui else 12)
        self._populate_staff_availability(staff_list)

        self._layout_schedule_columns(body, left_card, right_col)
        body.bind(
            "<Configure>",
            lambda _e, container=body, left=left_card, right=right_col: self._layout_schedule_columns(
                container, left, right
            ),
            add="+",
        )

    @staticmethod
    def _validate_iso_date_input(proposed):
        if proposed == "":
            return True
        if len(proposed) > 10:
            return False
        for index, char in enumerate(proposed):
            if index in (4, 7):
                if char != "-":
                    return False
            elif not char.isdigit():
                return False
        return True

    def _layout_schedule_columns(self, body, left_card, right_col):
        if not (body.winfo_exists() and left_card.winfo_exists() and right_col.winfo_exists()):
            return

        width = int(body.winfo_width() or 0)
        root = self.winfo_toplevel()
        root_height = int(root.winfo_height() or 0)
        compact = width < 1750 or (0 < root_height < 980)

        # Keep the original side-by-side layout for this screen.
        # Compact mode only reduces spacing/relative width balance.
        left_pad = (0, 8) if compact else (0, 10)
        left_weight = 12 if compact else 11
        right_weight = 9 if compact else 10

        left_card.grid_configure(row=0, column=0, sticky="nsew", padx=left_pad, pady=0, columnspan=1)
        right_col.grid_configure(row=0, column=1, sticky="nsew", padx=0, pady=0, columnspan=1)
        body.grid_columnconfigure(0, weight=left_weight)
        body.grid_columnconfigure(1, weight=right_weight)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=0)

    def _schedule_timeline_text(self):
        if not self.selected_request_id:
            return "Select a request from All Requests to see timeline details."

        row = self.request_rows_by_id.get(str(self.selected_request_id), {})
        if not row:
            return "No timeline data available for the selected request."

        events = []
        created = self._format_db_datetime(row.get("created_at"))
        updated = self._format_db_datetime(row.get("updated_at"))
        scheduled_date = str(row.get("scheduled_date", "") or "").strip()
        scheduled_time = str(row.get("scheduled_time", "") or "").strip()
        status = self._format_status_display(row.get("status", ""))

        if created:
            events.append(f"Created: {created}")
        if scheduled_date or scheduled_time:
            schedule_bits = " ".join(part for part in [scheduled_date, scheduled_time] if part).strip()
            events.append(f"Scheduled: {schedule_bits}")
        events.append(f"Current status: {status}")
        if updated:
            events.append(f"Last updated: {updated}")
        return "\n".join(events)

    def _format_db_datetime(self, value):
        text = str(value or "").strip()
        if not text:
            return ""
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).strftime("%d %b %Y %H:%M" if fmt.endswith("%S") else "%d %b %Y")
            except ValueError:
                continue
        return text

    def _populate_staff_availability(self, parent):
        city = AuthController.get_current_location()
        current_city = None if str(city or "").strip().lower() == "all cities" else city
        try:
            staff_rows = [dict(row) for row in UserDAO.get_active_maintenance_staff(current_city)]
        except Exception:
            staff_rows = []

        if not staff_rows:
            ctk.CTkLabel(
                parent,
                text="No active maintenance staff found for this location.",
                text_color="#8E7E67",
                font=("Arial", 12),
                anchor="w",
            ).pack(fill="x")
            return

        job_counts = {}
        for row in self.all_request_rows:
            status = str(row.get("status", "")).strip().lower()
            if status in {"resolved", "closed"}:
                continue
            staff_name = str(row.get("assigned_staff", "")).strip().lower()
            if not staff_name:
                continue
            job_counts[staff_name] = job_counts.get(staff_name, 0) + 1

        current_user = AuthController.current_user or {}
        my_name = str(self._read_user_value(current_user, "full_name", "")).strip().lower()

        for staff in staff_rows[:5]:
            full_name = str(staff.get("full_name") or staff.get("username") or "Staff").strip()
            short_name = "".join(part[0] for part in full_name.split()[:2]).upper() or "MS"
            active_jobs = job_counts.get(full_name.lower(), 0)
            is_me = bool(my_name) and full_name.lower() == my_name

            if active_jobs == 0:
                chip_text = "Available"
                chip_bg = "#E2EFE2"
                chip_fg = "#2F6B3F"
            else:
                chip_text = f"{active_jobs} job active"
                chip_bg = "#F2E6CD"
                chip_fg = "#7A5A0A"

            row_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
            row_frame.pack(fill="x", pady=2)

            avatar = ctk.CTkLabel(
                row_frame,
                text=short_name,
                width=38,
                height=38,
                corner_radius=19,
                fg_color="#E9EFE9" if is_me else "#F3F0E8",
                text_color="#2F6B3F" if is_me else "#7A5A0A",
                font=("Arial", 14, "bold"),
            )
            avatar.pack(side="left")

            name_text = f"{full_name} (you)" if is_me else full_name
            ctk.CTkLabel(
                row_frame,
                text=name_text,
                text_color=self.TEXT_MAIN,
                font=("Arial", 12, "bold" if is_me else "normal"),
                anchor="w",
            ).pack(side="left", padx=(8, 10), fill="x", expand=True)

            ctk.CTkLabel(
                row_frame,
                text=chip_text,
                fg_color=chip_bg,
                text_color=chip_fg,
                corner_radius=12,
                width=96,
                height=24,
                font=("Arial", 11, "bold"),
            ).pack(side="right")

    def _build_resolve_section(self, parent):
        if self.current_role not in ("maintenance",):
            return
        root = self.winfo_toplevel()
        root.update_idletasks()
        compact_ui = int(root.winfo_height() or 0) < 980
        header_font = 15 if compact_ui else 17
        role_font = 12 if compact_ui else 14
        label_font = 9 if compact_ui else 10
        input_height = 34 if compact_ui else 40
        text_height = 110 if compact_ui else 150
        card_pad = 12 if compact_ui else 16

        warning = ctk.CTkFrame(
            parent,
            fg_color="#F5ECD5",
            corner_radius=14,
            border_width=1,
            border_color="#E2CF9F",
        )
        warning.pack(fill="x", pady=(0, 12))
        warning_text = (
            "No request selected. Go to All Requests, click a row, then return here."
            if not self.selected_request_id
            else f"Ready to resolve {self.selected_id_var.get()}."
        )
        ctk.CTkLabel(
            warning,
            text=f"⚠ {warning_text}",
            text_color="#7A5A0A",
            font=("Arial", 12 if compact_ui else 13, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=10 if compact_ui else 12)

        layout = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        layout.pack(fill="both", expand=True)
        layout.grid_columnconfigure(0, weight=11)
        layout.grid_columnconfigure(1, weight=10)

        resolve_frame = ctk.CTkFrame(
            layout,
            fg_color=self.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        resolve_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        resolve_frame.grid_columnconfigure(0, weight=1)
        resolve_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            resolve_frame,
            text="Resolve Request",
            text_color=self.TEXT_MAIN,
            font=("Arial", header_font, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=card_pad, pady=(10 if compact_ui else 14, 6 if compact_ui else 8))
        ctk.CTkLabel(
            resolve_frame,
            text="Maintenance Staff only",
            text_color="#4D8A56",
            font=("Arial", role_font),
            anchor="e",
        ).grid(row=0, column=1, sticky="e", padx=card_pad, pady=(10 if compact_ui else 14, 6 if compact_ui else 8))

        ctk.CTkFrame(resolve_frame, fg_color="#ECE1CD", corner_radius=0, height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew"
        )

        form = ctk.CTkFrame(resolve_frame, fg_color="transparent", corner_radius=0)
        form.grid(row=2, column=0, columnspan=2, sticky="ew", padx=card_pad, pady=(10 if compact_ui else 12, 10 if compact_ui else 14))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            form,
            text="RESOLUTION NOTE",
            text_color="#9A8A70",
            font=("Arial", label_font, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.resolution_text = ctk.CTkTextbox(
            form,
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            text_color=self.TEXT_MAIN,
            corner_radius=10,
            height=text_height,
            font=("Arial", 12 if compact_ui else 13),
            wrap="word",
        )
        self.resolution_text.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8 if compact_ui else 10))

        self._resolve_placeholder = "What was done? Parts used? Any follow-up needed?"
        self._set_textbox_placeholder(self.resolution_text, self._resolve_placeholder)
        self.resolution_text.bind(
            "<FocusIn>",
            lambda e: self._clear_textbox_placeholder(self.resolution_text, self._resolve_placeholder),
        )
        self.resolution_text.bind(
            "<FocusOut>",
            lambda e: self._restore_textbox_placeholder(self.resolution_text, self._resolve_placeholder),
        )

        ctk.CTkLabel(
            form,
            text="HOURS SPENT",
            text_color="#9A8A70",
            font=("Arial", label_font, "bold"),
            anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(0, 4))
        ctk.CTkLabel(
            form,
            text="ACTUAL COST (£)",
            text_color="#9A8A70",
            font=("Arial", label_font, "bold"),
            anchor="w",
        ).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(0, 4))

        ctk.CTkEntry(
            form,
            textvariable=self.hours_spent_var,
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            text_color=self.TEXT_MAIN,
            corner_radius=10,
            height=input_height,
            font=("Arial", 12 if compact_ui else 13),
        ).grid(row=3, column=0, sticky="ew", pady=(0, 8 if compact_ui else 12))

        ctk.CTkEntry(
            form,
            textvariable=self.cost_var,
            fg_color="#FFFFFF",
            border_color="#DCCEB8",
            border_width=1,
            text_color=self.TEXT_MAIN,
            corner_radius=10,
            height=input_height,
            font=("Arial", 12 if compact_ui else 13),
        ).grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(0, 8 if compact_ui else 12))

        actions = ctk.CTkFrame(form, fg_color="transparent", corner_radius=0)
        actions.grid(row=4, column=0, columnspan=2, sticky="w")

        ctk.CTkButton(
            actions,
            text="Mark as\nResolved",
            command=self.resolve_selected_request,
            fg_color="#3E7B45",
            hover_color="#2F6436",
            text_color="#FFFFFF",
            border_width=0,
            corner_radius=12,
            height=44 if compact_ui else 56,
            width=150 if compact_ui else 170,
            font=("Arial", 12 if compact_ui else 13, "bold"),
        ).pack(side="left", padx=(0, 8 if compact_ui else 10))

        ctk.CTkButton(
            actions,
            text="←\nBack",
            command=lambda: self.show_section("requests"),
            fg_color="#F8F5F0",
            hover_color="#EEE4D2",
            text_color="#1E1B15",
            border_width=1,
            border_color="#BFB5A5",
            corner_radius=12,
            height=44 if compact_ui else 56,
            width=88 if compact_ui else 96,
            font=("Arial", 12 if compact_ui else 13, "bold"),
        ).pack(side="left")

        summary = ctk.CTkFrame(
            layout,
            fg_color=self.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        summary.grid(row=0, column=1, sticky="nsew")
        self._build_resolve_summary(summary, compact_ui=compact_ui)

    def _build_resolve_summary(self, parent, compact_ui=False):
        current_user = AuthController.current_user or {}
        my_name = (
            self._read_user_value(current_user, "full_name")
            or self._read_user_value(current_user, "username")
            or "Maintenance Staff"
        )
        name_key = str(my_name).strip().lower()

        resolved_rows = [
            row for row in self.all_request_rows
            if str(row.get("status", "")).strip().lower() == "resolved"
        ]
        mine = [
            row for row in resolved_rows
            if str(row.get("assigned_staff", "")).strip().lower() == name_key
        ]

        jobs_resolved = len(mine)
        total_cost = sum(self._safe_float(row.get("cost", 0)) for row in mine)
        total_hours = sum(self._safe_float(row.get("hours_spent", 0)) for row in mine)
        avg_cost = (total_cost / jobs_resolved) if jobs_resolved else 0.0

        ctk.CTkLabel(
            parent,
            text="Your Cost Summary",
            text_color=self.TEXT_MAIN,
            font=("Arial", 15 if compact_ui else 17, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12 if compact_ui else 16, pady=(10 if compact_ui else 14, 6 if compact_ui else 8))
        ctk.CTkButton(
            parent,
            text="Full report",
            command=self.show_report,
            fg_color="transparent",
            hover_color="#F5EFE4",
            text_color="#2F6B3F",
            corner_radius=10,
            height=26 if compact_ui else 28,
            width=84 if compact_ui else 90,
            font=("Arial", 11 if compact_ui else 12, "bold"),
        ).place(relx=1.0, x=-(12 if compact_ui else 14), y=10 if compact_ui else 14, anchor="ne")
        ctk.CTkFrame(parent, fg_color="#ECE1CD", corner_radius=0, height=1).pack(fill="x")

        score = ctk.CTkFrame(
            parent,
            fg_color="#EEF3EA",
            corner_radius=14,
            border_width=1,
            border_color="#9FCC9F",
        )
        score.pack(fill="x", padx=12 if compact_ui else 16, pady=(8 if compact_ui else 12, 8 if compact_ui else 10))

        ctk.CTkLabel(
            score,
            text=f"{my_name} — YTD Performance",
            text_color=self.TEXT_MAIN,
            font=("Arial", 13 if compact_ui else 15, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12 if compact_ui else 14, pady=(10 if compact_ui else 12, 6 if compact_ui else 8))

        for label, value in [
            ("Jobs Resolved", str(jobs_resolved)),
            ("Total Cost Logged", f"£{total_cost:,.2f}"),
            ("Total Labour Hours", f"{total_hours:.1f} hrs"),
            ("Avg Cost / Job", f"£{avg_cost:,.2f}"),
        ]:
            row = ctk.CTkFrame(score, fg_color="transparent", corner_radius=0, height=24)
            row.pack(fill="x", padx=12 if compact_ui else 14, pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=label, text_color="#5E5137", font=("Arial", 11 if compact_ui else 12, "bold"), anchor="w").pack(
                side="left", fill="x", expand=True
            )
            ctk.CTkLabel(row, text=value, text_color=self.TEXT_MAIN, font=("Arial", 11 if compact_ui else 12, "bold"), anchor="e").pack(
                side="right"
            )
        ctk.CTkFrame(score, fg_color="transparent", height=6 if compact_ui else 10).pack()

        ctk.CTkLabel(
            parent,
            text="YOUR JOBS BY CATEGORY",
            text_color="#9A8A70",
            font=("Arial", 9 if compact_ui else 10, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12 if compact_ui else 16, pady=(0 if compact_ui else 2, 3 if compact_ui else 4))

        categories = self._resolve_category_totals(mine)
        max_value = max([value for _, value in categories] + [1.0])
        for idx, (label, amount) in enumerate(categories):
            is_last = idx == len(categories) - 1
            row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
            row.pack(
                fill="x",
                padx=12 if compact_ui else 16,
                pady=(2 if compact_ui else 3, 8 if is_last else (2 if compact_ui else 3)),
            )
            top = ctk.CTkFrame(row, fg_color="transparent", corner_radius=0)
            top.pack(fill="x")
            ctk.CTkLabel(top, text=label, text_color=self.TEXT_MAIN, font=("Arial", 11 if compact_ui else 12, "bold"), anchor="w").pack(
                side="left", fill="x", expand=True
            )
            ctk.CTkLabel(top, text=f"£{amount:,.0f}", text_color=self.TEXT_MAIN, font=("Arial", 11 if compact_ui else 12, "bold"), anchor="e").pack(
                side="right"
            )
            rail = ctk.CTkFrame(row, fg_color="#E6DDCC", corner_radius=4, height=7 if compact_ui else 8)
            rail.pack(fill="x", pady=(2, 0))
            fill_width = max(0.05, amount / max_value)
            ctk.CTkFrame(
                rail,
                fg_color="#3E7B45",
                corner_radius=4,
                height=7 if compact_ui else 8,
                width=max(8, int((300 if compact_ui else 370) * fill_width)),
            ).pack(
                side="left"
            )

    def _resolve_category_totals(self, rows):
        categories = {
            "Plumbing": 0.0,
            "Heating / HVAC": 0.0,
            "Windows / Locks": 0.0,
        }
        for row in rows:
            title = str(row.get("title", "")).strip().lower()
            cost = self._safe_float(row.get("cost", 0))
            if any(token in title for token in ("pipe", "plumb", "leak", "drain", "toilet", "tap", "water")):
                categories["Plumbing"] += cost
            elif any(token in title for token in ("heater", "heating", "boiler", "hvac", "ac", "air", "vent")):
                categories["Heating / HVAC"] += cost
            else:
                categories["Windows / Locks"] += cost
        return list(categories.items())

    def create_request(self):
        if self.current_role not in ("front_desk", "admin"):
            messagebox.showwarning("Access Denied", "You do not have access to create requests.")
            return

        try:
            apartment_id_text = self.create_apartment_id_var.get().strip()
            if apartment_id_text == "Auto-populated":
                apartment_id_text = ""

            selected_label = self.create_tenant_var.get().strip()
            title = self.create_title_var.get().strip()
            description = self.create_description_text.get("1.0", tk.END).strip()
            if description == self._create_desc_placeholder:
                description = ""

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
                status="Open",
            )

            messagebox.showinfo("Created", "Maintenance request created successfully.")

            self.create_apartment_id_var.set("Auto-populated")
            self.create_tenant_var.set("Select tenant...")
            if hasattr(self, "tenant_dropdown"):
                self.tenant_dropdown.set("Select tenant...")
            self.create_title_var.set("")
            self._set_textbox_placeholder(
                self.create_description_text,
                self._create_desc_placeholder
            )
            self.create_priority_combo.set("Medium")

            self.show_section("requests")

        except ValueError:
            messagebox.showwarning("Invalid Input", "Apartment ID must be numeric if present.")

    def load_data(self):
        rows = self.dao.get_all_requests()
        self._refresh_summary_cards(rows)
        self.all_request_rows = rows
        self.request_rows_by_id = {str(row.get("requestID", "")): row for row in rows}

        if self.request_list_body is not None and self.request_list_body.winfo_exists():
            self._populate_request_cards(self._get_filtered_rows())
            return

        if self.tree is None or not self.tree.winfo_exists():
            return

        self._populate_request_tree(self._get_filtered_rows())

    def _populate_request_tree(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            scheduled_date = str(row.get("scheduled_date", "") or "").strip()
            scheduled_time = str(row.get("scheduled_time", "") or "").strip()

            if scheduled_date and scheduled_time:
                scheduled_display = f"{scheduled_date} {scheduled_time}"
            elif scheduled_date:
                scheduled_display = scheduled_date
            elif scheduled_time:
                scheduled_display = scheduled_time
            else:
                scheduled_display = "-"

            cost_value = self._safe_float(row.get("cost", 0))
            hours_value = self._safe_float(row.get("hours_spent", 0))

            request_id = row.get("requestID", "")
            if request_id not in ("", None):
                request_id = f"MNT-{int(request_id):04d}"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    request_id,
                    row.get("title", "") or "-",
                    self._format_priority_display(row.get("priority", "")),
                    self._format_status_display(row.get("status", "")),
                    row.get("assigned_staff", "") or "-",
                    scheduled_display,
                    f"£{cost_value:,.2f}" if cost_value > 0 else "-",
                    f"{hours_value:.1f}" if hours_value > 0 else "-",
                ),
                tags=(self._get_row_tag(row),),
            )

        self.selected_request_id = None
        self.selected_id_var.set("None")

    def _format_status_display(self, status):
        value = str(status or "").strip().lower()
        mapping = {
            "open": "Open",
            "scheduled": "Scheduled",
            "in progress": "In Progress",
            "in_progress": "In Progress",
            "resolved": "Resolved",
        }
        return mapping.get(value, str(status or "-").strip() or "-")


    def _format_priority_display(self, priority):
        value = str(priority or "").strip().lower()
        mapping = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
            "urgent": "Urgent",
        }
        return mapping.get(value, str(priority or "-").strip() or "-")


    def _get_row_tag(self, row):
        status = str(row.get("status", "")).strip().lower()
        priority = str(row.get("priority", "")).strip().lower()

        if status == "resolved":
            return "resolved_row"
        if priority == "urgent":
            return "urgent_row"
        if priority == "high":
            return "high_row"
        if priority == "low":
            return "low_row"
        return "medium_row"

    def _get_filtered_rows(self):
        selected_status = self.status_filter_var.get().strip().lower()
        filtered_rows = list(self.all_request_rows)

        if selected_status not in ("", "all statuses"):
            filtered_rows = [
                row for row in filtered_rows
                if str(row.get("status", "")).strip().lower() == selected_status
            ]

        query = str(getattr(self, "_search_query", "") or "").strip().lower()
        if not query:
            return filtered_rows

        results = []
        for row in filtered_rows:
            scheduled_date = str(row.get("scheduled_date", "") or "").strip()
            scheduled_time = str(row.get("scheduled_time", "") or "").strip()
            scheduled_display = " ".join(part for part in (scheduled_date, scheduled_time) if part).strip()
            request_id = row.get("requestID", "")
            request_id_label = ""
            if request_id not in ("", None):
                try:
                    request_id_label = f"MNT-{int(request_id):04d}"
                except (TypeError, ValueError):
                    request_id_label = str(request_id)

            haystack = " ".join(
                [
                    str(row.get("title", "") or ""),
                    str(row.get("description", "") or ""),
                    str(row.get("priority", "") or ""),
                    str(row.get("status", "") or ""),
                    str(row.get("assigned_staff", "") or ""),
                    str(row.get("tenant_name", "") or ""),
                    str(row.get("apartmentID", "") or ""),
                    str(row.get("cost", "") or ""),
                    str(row.get("hours_spent", "") or ""),
                    str(scheduled_display or ""),
                    request_id_label,
                ]
            ).lower()

            if query in haystack:
                results.append(row)

        return results

    def _on_shell_search(self, query=None):
        if isinstance(query, str):
            self._search_query = query.strip()
        else:
            self._search_query = ""
        self.apply_request_filter()

    def apply_request_filter(self, _event=None):
        if self.request_list_body is not None and self.request_list_body.winfo_exists():
            self._populate_request_cards(self._get_filtered_rows())
            return

        if self.tree is None or not self.tree.winfo_exists():
            return
        self._populate_request_tree(self._get_filtered_rows())

    def on_select_request(self, _event=None, request_id=None, display_id=None):
        if request_id is not None:
            raw_id = str(request_id).strip()
            if not raw_id:
                self.selected_request_id = None
                self.selected_id_var.set("None")
                return
            self.selected_request_id = raw_id
            if display_id:
                self.selected_id_var.set(display_id)
            else:
                try:
                    self.selected_id_var.set(f"MNT-{int(raw_id):04d}")
                except ValueError:
                    self.selected_id_var.set(raw_id)
            self._set_selected_request_card(raw_id)
        else:
            selected = self.tree.selection() if self.tree is not None else []
            if not selected:
                self.selected_request_id = None
                self.selected_id_var.set("None")
                return

            values = self.tree.item(selected[0], "values")
            selected_display = str(values[0]).strip()
            raw_id = selected_display.replace("MNT-", "").lstrip("0")
            self.selected_request_id = raw_id if raw_id else "0"
            self.selected_id_var.set(selected_display)

        selected_row = self.request_rows_by_id.get(self.selected_request_id, {})

        assigned_staff = selected_row.get("assigned_staff", "") or ""
        scheduled_date = selected_row.get("scheduled_date", "") or ""
        scheduled_time = selected_row.get("scheduled_time", "") or ""
        priority = selected_row.get("priority", "") or "Medium"

        self.assigned_staff_var.set(assigned_staff)
        self.scheduled_date_var.set(scheduled_date)
        self.scheduled_time_var.set(scheduled_time)
        self.schedule_priority_var.set(priority)

        if self.priority_combo is not None and self.priority_combo.winfo_exists():
            self.priority_combo.set(priority)

        self.hours_spent_var.set(str(self._safe_float(selected_row.get("hours_spent", 0))))
        self.cost_var.set(str(self._safe_float(selected_row.get("cost", 0))))

    def schedule_selected_request(self):
        if self.current_role not in ("maintenance",):
            messagebox.showwarning("Access Denied", "You do not have access to schedule requests.")
            return

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
                "Please enter assigned staff, scheduled date, and scheduled time.",
            )
            return

        try:
            datetime.strptime(scheduled_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Invalid Date",
                "Scheduled date must be in YYYY-MM-DD format (for example 2026-04-23).",
            )
            return

        self.dao.schedule_request(
            self.selected_request_id,
            assigned_staff,
            scheduled_date,
            scheduled_time,
            priority,
        )
        messagebox.showinfo("Updated", "Request scheduled successfully.")
        self.load_data()

    def resolve_selected_request(self):
        if self.current_role not in ("maintenance",):
            messagebox.showwarning("Access Denied", "You do not have access to resolve requests.")
            return

        # Mark the selected request as resolved and save time/cost details.
        if not self.selected_request_id:
            messagebox.showwarning("No Selection", "Please select a maintenance request first.")
            return

        resolution_note = self.resolution_text.get("1.0", tk.END).strip()
        if resolution_note == getattr(self, "_resolve_placeholder", ""):
            resolution_note = ""

        try:
            hours_spent = float(self.hours_spent_var.get().strip() or 0)
            cost = float(self.cost_var.get().strip() or 0)
        except ValueError:
            messagebox.showwarning("Invalid Input", "Hours and cost must be numeric.")
            return

        self.dao.resolve_request(self.selected_request_id, resolution_note, hours_spent, cost)
        messagebox.showinfo("Resolved", "Request marked as resolved.")
        self.resolution_text.delete("1.0", tk.END)
        self.load_data()

    def show_report(self):
        # Show a simple maintenance cost summary report.
        total, hours, count = self.dao.get_cost_report_data()
        report = f"Resolved Tasks: {count}\nTotal Cost: £{total:.2f}\nTotal Labour: {hours:.1f} hrs"
        messagebox.showinfo("Maintenance Cost Report", report)

    def _initial_notification_count(self):
        try:
            rows = self.dao.get_all_requests()
            return sum(
                1
                for row in rows
                if str(row.get("priority", "")).strip().lower() in {"urgent", "high"}
                and str(row.get("status", "")).strip().lower() not in {"resolved", "closed"}
            )
        except Exception:
            return 0

    def _show_alerts(self):
        rows = self.all_request_rows if self.all_request_rows else self.dao.get_all_requests()
        high_priority_open = 0
        scheduled_count = 0
        unresolved_count = 0

        for row in rows:
            status = str(row.get("status", "")).strip().lower()
            priority = str(row.get("priority", "")).strip().lower()

            if status not in {"resolved", "closed"}:
                unresolved_count += 1
            if priority in {"urgent", "high"} and status not in {"resolved", "closed"}:
                high_priority_open += 1
            if status in {"scheduled", "in progress", "in_progress"}:
                scheduled_count += 1

        self.shell.show_premium_info_modal(
            title="Maintenance Alerts",
            icon_text="🔔",
            icon_fg="#B8891F",
            icon_bg="#F6E8B8",
            highlight_nonzero=True,
            rows=[
                ("High-priority open requests", str(high_priority_open)),
                ("Scheduled / in progress", str(scheduled_count)),
                ("Total active requests", str(unresolved_count)),
            ],
        )

    def _show_settings(self):
        current_user = AuthController.current_user
        full_name = (
            self._read_user_value(current_user, "full_name")
            or self._read_user_value(current_user, "username")
            or "User"
        )
        role_value = self._read_user_value(current_user, "role_name") or self.current_role or "-"
        role_text = str(role_value).replace("_", " ").title()
        location = self._read_user_value(current_user, "location") or AuthController.get_current_location() or "All Cities"
        is_admin = str(role_value).strip().lower() == "admin"

        rows = [
            ("User", str(full_name)),
            ("Role", role_text),
        ]
        if is_admin:
            rows.append(("Location Access", "Full location access (All Cities)"))
        else:
            rows.append(("Location", str(location)))

        self.shell.show_premium_info_modal(
            title="Account Settings",
            icon_bg="#F6EED7",
            rows=rows,
            icon_image_name="settings",
            icon_image_size=(34, 34),
        )

    def export_requests_csv(self):
        rows = self._get_filtered_rows()
        if not rows:
            messagebox.showinfo("No Data", "There are no requests to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Maintenance Requests",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="maintenance_requests.csv",
        )
        if not file_path:
            return

        fields = [
            "requestID",
            "tenant_name",
            "apartmentID",
            "title",
            "priority",
            "status",
            "assigned_staff",
            "scheduled_date",
            "scheduled_time",
            "hours_spent",
            "cost",
        ]
        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in fields})

        self.shell.show_premium_info_modal(
            title="Export Complete",
            rows=[("CSV exported to", file_path)],
            icon_image_name="success",
            icon_image_size=(34, 34),
            button_text="OK",
        )

    def auto_fill_apartment_from_tenant(self, _event=None):
        selected_label = self.create_tenant_var.get().strip()

        if not selected_label or selected_label == "Select tenant...":
            self.create_apartment_id_var.set("Auto-populated")
            return

        tenant_id = None
        for item in self.tenant_options:
            if item["label"] == selected_label:
                tenant_id = item["tenantID"]
                break

        if tenant_id is None:
            self.create_apartment_id_var.set("Auto-populated")
            return

        apartment_id = self.dao.get_current_apartment_by_tenant(tenant_id)
        self.create_apartment_id_var.set("Auto-populated" if apartment_id is None else str(apartment_id))


class MaintenanceView(MaintenanceDashboardView):
    # Backward-compatible alias if older imports still use MaintenanceView.
    pass


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    root.minsize(900, 650)
    root.resizable(True, True)

    app = MaintenanceDashboardView(root)
    root.mainloop()
