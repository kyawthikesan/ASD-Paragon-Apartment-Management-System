# Student Name: Kyaw Thike (oliver) San
# Student ID: 25014001
# Module: UFCF8S-30-2 Advanced Software Development
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import customtkinter as ctk

from dao.maintenance_dao import MaintenanceDAO
from controllers.auth_controller import AuthController
from views.premium_shell import PremiumAppShell
from tkcalendar import DateEntry


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

        self._apply_local_styles()
        self.shell = PremiumAppShell(
            self,
            page_title="Maintenance",
            on_logout=self.home_callback or self.logout_callback,
            active_nav="Maintenance",
            nav_sections=self._build_nav_sections(),
            footer_action_label="Back to Dashboard" if self.home_callback else "Logout",
            search_placeholder="Search maintenance requests...",
            location_label=AuthController.get_current_location(),
            on_bell_click=self._show_alerts,
            on_settings_click=self._show_settings,
            notification_count=self._initial_notification_count(),
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
            finance_action = self.open_finance_payments or self.open_finance_reports
            nav_sections[2]["items"].append(
                {"label": "Payments & Reports", "action": finance_action, "icon": "payments"}
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

    def _build_summary_row(self):
        row = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=0)
        row.pack(fill="x", padx=18, pady=(0, 10))

        for i in range(4):
            row.grid_columnconfigure(i, weight=1)

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

        schedule_frame = ttk.LabelFrame(parent, text="Schedule / Update Request", style="Maintenance.TLabelframe", padding=14)
        schedule_frame.pack(fill="x")

        ttk.Label(
            schedule_frame,
            text="Select a request first from 'Maintenance Req'.",
            style="Maintenance.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 10))

        ttk.Label(schedule_frame, text="Selected Request ID", style="Maintenance.TLabel").grid(
            row=1, column=0, sticky="w", padx=6, pady=6
        )
        ttk.Label(schedule_frame, textvariable=self.selected_id_var, style="Maintenance.TLabel").grid(
            row=1, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(schedule_frame, text="Assigned Staff", style="Maintenance.TLabel").grid(
            row=2, column=0, sticky="w", padx=6, pady=6
        )
        ttk.Entry(
            schedule_frame,
            textvariable=self.assigned_staff_var,
            width=24,
            style="Maintenance.TEntry",
        ).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(schedule_frame, text="Scheduled Date", style="Maintenance.TLabel").grid(
            row=3, column=0, sticky="w", padx=6, pady=6
        )
        self.date_picker = DateEntry(
            schedule_frame,
            textvariable=self.scheduled_date_var,
            width=21,
            date_pattern="yyyy-mm-dd",
        )
        self.date_picker.grid(row=3, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(schedule_frame, text="Scheduled Time", style="Maintenance.TLabel").grid(
            row=4, column=0, sticky="w", padx=6, pady=6
        )

        time_values = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in (0, 15, 30, 45)]

        self.time_combo = ttk.Combobox(
            schedule_frame,
            textvariable=self.scheduled_time_var,
            state="readonly",
            values=time_values,
            width=21,
            style="Maintenance.TCombobox",
        )
        self.time_combo.grid(row=4, column=1, sticky="w", padx=6, pady=6)

        if not self.scheduled_time_var.get().strip():
            self.scheduled_time_var.set("09:00")

        ttk.Label(schedule_frame, text="Priority", style="Maintenance.TLabel").grid(
            row=5, column=0, sticky="w", padx=6, pady=6
        )

        self.priority_combo = ttk.Combobox(
            schedule_frame,
            textvariable=self.schedule_priority_var,
            state="readonly",
            values=["Low", "Medium", "High", "Urgent"],
            width=21,
            style="Maintenance.TCombobox",
        )
        self.priority_combo.grid(row=5, column=1, sticky="w", padx=6, pady=6)
        self.priority_combo.set(self.schedule_priority_var.get())

        ttk.Button(
            schedule_frame,
            text="Schedule Request",
            command=self.schedule_selected_request,
            style="Maintenance.Primary.TButton",
        ).grid(row=6, column=1, sticky="w", padx=6, pady=(10, 0))

    def _build_resolve_section(self, parent):
        if self.current_role not in ("maintenance",):
            return

        resolve_frame = ttk.LabelFrame(parent, text="Resolve Request", style="Maintenance.TLabelframe", padding=14)
        resolve_frame.pack(fill="x")

        ttk.Label(
            resolve_frame,
            text="Select a request first from 'Maintenance Req'.",
            style="Maintenance.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 10))

        ttk.Label(resolve_frame, text="Selected Request ID", style="Maintenance.TLabel").grid(
            row=1, column=0, sticky="w", padx=6, pady=6
        )
        ttk.Label(resolve_frame, textvariable=self.selected_id_var, style="Maintenance.TLabel").grid(
            row=1, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(resolve_frame, text="Resolution Note", style="Maintenance.TLabel").grid(
            row=2, column=0, sticky="nw", padx=6, pady=6
        )
        self.resolution_text = tk.Text(
            resolve_frame,
            width=44,
            height=6,
            relief="solid",
            bd=1,
            bg="#FFFFFF",
            fg=self.TEXT_MAIN,
            highlightthickness=1,
            highlightbackground="#DCCEB8",
            insertbackground=self.GOLD_DEEP,
        )
        self.resolution_text.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(resolve_frame, text="Hours Spent", style="Maintenance.TLabel").grid(
            row=3, column=0, sticky="w", padx=6, pady=6
        )
        ttk.Entry(
            resolve_frame,
            textvariable=self.hours_spent_var,
            width=18,
            style="Maintenance.TEntry",
        ).grid(row=3, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(resolve_frame, text="Cost", style="Maintenance.TLabel").grid(
            row=4, column=0, sticky="w", padx=6, pady=6
        )
        ttk.Entry(
            resolve_frame,
            textvariable=self.cost_var,
            width=18,
            style="Maintenance.TEntry",
        ).grid(row=4, column=1, sticky="w", padx=6, pady=6)

        ttk.Button(
            resolve_frame,
            text="Mark as Resolved",
            command=self.resolve_selected_request,
            style="Maintenance.Primary.TButton",
        ).grid(row=5, column=1, sticky="w", padx=6, pady=(10, 0))

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
        if selected_status in ("", "all statuses"):
            return list(self.all_request_rows)
        return [
            row for row in self.all_request_rows
            if str(row.get("status", "")).strip().lower() == selected_status
        ]

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

        messagebox.showinfo("Export Complete", f"CSV exported to:\n{file_path}")

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
