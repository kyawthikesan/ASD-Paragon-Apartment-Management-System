# Student Name: Nang Phwe Hleng Hun
# Student ID: 24043841
# Module: UFCF8S-30-2 Advanced Software Development

# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

import tkinter as tk
from tkinter import ttk, filedialog
from datetime import date, datetime, timedelta
import os

import customtkinter as ctk
from tkcalendar import DateEntry, Calendar
try:
    from PIL import Image
except Exception:
    Image = None

from controllers.auth_controller import AuthController
from controllers.lease_controller import LeaseController
from dao.apartment_dao import ApartmentDAO
from dao.lease_dao import LeaseDAO
from dao.tenant_dao import TenantDAO
from views.premium_shell import PremiumAppShell


class LeaseView(tk.Frame):
    PAGE_BG = "#F8F5F0"
    CARD_BG = "#FFFFFF"
    CARD_TINT = "#FFFEFC"
    BORDER = "#E2D7C5"
    BORDER_SOFT = "#EFE5D5"
    TEXT = "#2B2419"
    MUTED = "#7A6C57"
    LABEL = "#8F8068"
    ACCENT = "#C3A04B"
    ACCENT_HOVER = "#AF8F45"
    SURFACE_SOFT = "#F6F2EA"

    STATUS_STYLES = {
        "Active": {"bg": "#DBEBDD", "fg": "#2F6B3F", "bar": "#4A9B5A"},
        "Expiring Soon": {"bg": "#F4E8CF", "fg": "#8B692A", "bar": "#B48D39"},
        "Renewal Sent": {"bg": "#DDE9F8", "fg": "#2B5F95", "bar": "#4B84C4"},
        "Notice Given": {"bg": "#F3DDDD", "fg": "#8E3030", "bar": "#B64C4C"},
        "Expired": {"bg": "#ECE9E3", "fg": "#756954", "bar": "#A49783"},
    }

    FILTERS = ["All", "Active", "Expiring Soon", "Notice Given", "Renewal Sent", "Expired"]

    def __init__(
        self,
        parent,
        back_callback,
        open_user_management=None,
        open_tenant_management=None,
        open_apartment_management=None,
        open_maintenance_dashboard=None,
        open_finance_payments=None,
        open_finance_reports=None,
    ):
        super().__init__(parent, bg=self.PAGE_BG)
        self.pack(fill="both", expand=True)

        self.back_callback = back_callback
        self.open_user_management = open_user_management or back_callback
        self.open_tenant_management = open_tenant_management or back_callback
        self.open_apartment_management = open_apartment_management or back_callback
        self.open_maintenance_dashboard = open_maintenance_dashboard or back_callback
        self.open_finance_payments = open_finance_payments or back_callback
        self.open_finance_reports = open_finance_reports or back_callback
        self.city_scope = AuthController.get_city_scope()
        self.role = AuthController.get_current_role()
        self.can_create_leases = AuthController.can_perform_action("create_leases", self.role)

        self.active_filter = "All"
        self.search_text = ""
        self.leases = []
        self.filtered_leases = []
        self.selected_lease_id = None
        self.tenant_map = {}
        self.apartment_map = {}
        self.sent_reminder_lease_ids = set()
        self._is_compact = False
        self._is_stacked = False
        self._content_height = 0

        nav_sections = [
            {
                "title": "Overview",
                "items": [{"label": "Dashboard", "action": back_callback, "icon": "dashboard"}],
            },
            {
                "title": "Management",
                "items": [
                    {"label": "Tenants", "action": self.open_tenant_management, "icon": "tenants"},
                    {"label": "Apartments", "action": self.open_apartment_management, "icon": "apartments"},
                    {"label": "Leases", "action": lambda: None, "icon": "leases"},
                ],
            },
            {"title": "Finance", "items": []},
            {"title": "Admin", "items": []},
        ]

        if AuthController.can_access_feature("finance_dashboard", self.role):
            nav_sections[2]["items"].append(
                {
                    "label": "Payments & Reports",
                    "action": self.open_finance_payments,
                    "icon": "payments",
                }
            )
        if AuthController.can_access_feature("maintenance_management", self.role):
            nav_sections[1]["items"].append(
                {
                    "label": "Maintenance",
                    "action": self.open_maintenance_dashboard,
                    "icon": "maintenance",
                }
            )

        nav_sections[3]["items"].append(
            {"label": "User Access", "action": self.open_user_management, "icon": "shield"}
        )

        self.shell = PremiumAppShell(
            self,
            page_title="Lease Management",
            on_logout=back_callback,
            active_nav="Leases",
            nav_sections=nav_sections,
            footer_action_label="Back to Dashboard",
            search_placeholder="Search tenant, unit, city...",
            on_search_change=self._on_search_change,
            on_search_submit=self._on_search_change,
            on_bell_click=self._show_alerts,
            on_settings_click=self._show_settings,
        )
        self.content = self.shell.content

        self._build_ui()
        self.load_tenants()
        self.load_available_apartments()
        self.load_leases()
        self.content.bind("<Configure>", self._on_layout_resize, add="+")

    @staticmethod
    def _to_date(value):
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except Exception:
            return None

    def _make_date_entry(self, parent):
        styled_kwargs = {
            "date_pattern": "yyyy-mm-dd",
            "background": self.ACCENT,
            "foreground": self.TEXT,
            "borderwidth": 1,
            "headersbackground": "#EEE6D7",
            "headersforeground": self.TEXT,
            "normalbackground": "#FFFFFF",
            "normalforeground": self.TEXT,
            "weekendbackground": "#FAF7F0",
            "weekendforeground": self.TEXT,
            "othermonthbackground": "#FFFFFF",
            "othermonthforeground": "#A7977E",
            "othermonthwebackground": "#FAF7F0",
            "othermonthweforeground": "#A7977E",
            "selectbackground": self.ACCENT,
            "selectforeground": "#FFFFFF",
            "disabledforeground": "#B8AA95",
        }
        try:
            return DateEntry(parent, **styled_kwargs)
        except Exception:
            return DateEntry(parent, date_pattern="yyyy-mm-dd")

    @staticmethod
    def _get_date_entry_iso(date_entry):
        try:
            return date_entry.get_date().isoformat()
        except Exception:
            text_value = str(date_entry.get() or "").strip()
            return text_value

    def _open_calendar_picker(self, parent, date_var, min_date=None):
        picker = ctk.CTkToplevel(parent)
        picker.title("Select Date")
        picker.geometry("330x360")
        picker.resizable(False, False)
        picker.transient(parent)
        picker.grab_set()
        self._center_popup(picker, 330, 360)

        body = ctk.CTkFrame(
            picker,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER,
        )
        body.pack(fill="both", expand=True, padx=12, pady=12)

        current = self._to_date(date_var.get()) or date.today()
        cal = Calendar(
            body,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            mindate=min_date,
            background=self.ACCENT,
            foreground="#FFFFFF",
            headersbackground="#EEE6D7",
            headersforeground=self.TEXT,
            normalbackground="#FFFFFF",
            normalforeground=self.TEXT,
            weekendbackground="#FAF7F0",
            weekendforeground=self.TEXT,
            othermonthbackground="#FFFFFF",
            othermonthforeground="#A7977E",
            othermonthwebackground="#FAF7F0",
            othermonthweforeground="#A7977E",
            selectbackground=self.ACCENT,
            selectforeground="#FFFFFF",
        )
        cal.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        try:
            cal.selection_set(current)
        except Exception:
            pass

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.pack(fill="x", padx=8, pady=(4, 8))

        ctk.CTkButton(
            actions,
            text="Cancel",
            width=90,
            height=32,
            corner_radius=10,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 11, "bold"),
            command=picker.destroy,
        ).pack(side="right")

        def apply_date():
            date_var.set(cal.get_date())
            picker.destroy()

        ctk.CTkButton(
            actions,
            text="Select",
            width=90,
            height=32,
            corner_radius=10,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=apply_date,
        ).pack(side="right", padx=(0, 8))

    @staticmethod
    def _clamp(value, low=0, high=100):
        return max(low, min(high, value))

    @staticmethod
    def _initials(name):
        parts = [p for p in str(name).strip().split() if p]
        if not parts:
            return "NA"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    def _status_from_row(self, raw_status, days_left):
        status = str(raw_status or "").strip().lower()
        # Backward-compatibility: older early-termination records were saved as
        # "Ended" while keeping a future end_date. Treat these as Notice Given.
        if status == "ended" and days_left > 0:
            return "Notice Given"
        if "notice" in status:
            return "Notice Given"
        if "renewal" in status:
            return "Renewal Sent"
        if status == "ended" or days_left < 0:
            return "Expired"
        if days_left <= 30:
            return "Expiring Soon"
        if days_left <= 60:
            return "Renewal Sent"
        return "Active"

    def _format_date(self, value):
        parsed = self._to_date(value)
        if not parsed:
            return str(value)
        return parsed.strftime("%-d %b %Y")

    def _format_period(self, start_date, end_date):
        start = self._to_date(start_date)
        end = self._to_date(end_date)
        if not start or not end:
            return f"{start_date} - {end_date}"
        return f"{start.strftime('%b %y')} - {end.strftime('%b %y')}"

    def _duration_months(self, start_date, end_date):
        start = self._to_date(start_date)
        end = self._to_date(end_date)
        if not start or not end:
            return 0
        return max(1, round((end - start).days / 30.4))

    def _days_left(self, end_date):
        end = self._to_date(end_date)
        if not end:
            return 0
        return (end - date.today()).days

    def _progress(self, start_date, end_date):
        start = self._to_date(start_date)
        end = self._to_date(end_date)
        if not start or not end or end <= start:
            return 0
        total = (end - start).days
        elapsed = (date.today() - start).days
        pct = round((elapsed / total) * 100)
        return self._clamp(pct)

    def _lease_view_row(self, row):
        start = row.get("start_date")
        end = row.get("end_date")
        days_left = self._days_left(end)
        progress_pct = self._progress(start, end)
        status_label = self._status_from_row(row.get("status"), days_left)
        raw_status = str(row.get("status") or "").strip().lower()

        # Keep ended/expired leases visually consistent even if legacy data has
        # a future end_date.
        if status_label == "Expired":
            progress_pct = 100
            if raw_status == "ended" and days_left > 0:
                days_left = 0

        return {
            "leaseID": row.get("leaseID"),
            "tenantID": row.get("tenantID"),
            "tenant_name": row.get("tenant_name") or "Unknown Tenant",
            "apartmentID": row.get("apartmentID"),
            "apartment_type": row.get("apartment_type") or "Unit",
            "city": row.get("city") or "",
            "rent": float(row.get("rent") or 0),
            "start_date": start,
            "end_date": end,
            "status_raw": row.get("status") or "",
            "status_label": status_label,
            "days_left": days_left,
            "progress_pct": progress_pct,
            "duration_months": self._duration_months(start, end),
            "period": self._format_period(start, end),
            "initials": self._initials(row.get("tenant_name") or ""),
            "unit_line": f"Unit #{row.get('apartmentID')} · {row.get('apartment_type')}",
        }

    def _build_ui(self):
        self.root_wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        self.root_wrap.pack(fill="both", expand=True)

        self.stats_row = ctk.CTkFrame(self.root_wrap, fg_color="transparent")
        self.stats_row.pack(fill="x", pady=(2, 12))
        self.stat_order = [
            "ACTIVE LEASES",
            "EXPIRING IN 60 DAYS",
            "NOTICE GIVEN",
            "UP FOR RENEWAL",
            "AVG LEASE LENGTH",
        ]

        self.stat_values = {}
        self.stat_cards = {}
        self._make_stat_card("ACTIVE LEASES", "0")
        self._make_stat_card("EXPIRING IN 60 DAYS", "0", value_color="#8B692A")
        self._make_stat_card("NOTICE GIVEN", "0", value_color="#8E3030")
        self._make_stat_card("UP FOR RENEWAL", "0", value_color="#2B5F95")
        self._make_stat_card("AVG LEASE LENGTH", "0 mo")

        self.main = ctk.CTkFrame(self.root_wrap, fg_color="transparent")
        self.main.pack(fill="both", expand=True)
        self.main.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(
            self.main,
            fg_color=self.CARD_TINT,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER,
        )

        self.right_panel = ctk.CTkFrame(self.main, fg_color="transparent")
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()
        self._apply_responsive_layout()

    def _make_stat_card(self, label, value, value_color=None):
        card = ctk.CTkFrame(
            self.stats_row,
            fg_color=self.CARD_TINT,
            corner_radius=14,
            border_width=1,
            border_color=self.BORDER,
            height=82,
        )
        card.grid_propagate(False)

        ctk.CTkLabel(
            card,
            text=label,
            text_color="#96866A",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(9, 1))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            text_color=value_color or self.TEXT,
            font=("Georgia", 18, "bold"),
            anchor="w",
        )
        value_label.pack(fill="x", padx=12)
        self.stat_values[label] = value_label
        self.stat_cards[label] = card

    def _build_left_panel(self):
        header = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 8))

        ctk.CTkLabel(
            header,
            text="All Lease Agreements",
            text_color=self.TEXT,
            font=("Georgia", 24, "bold"),
            anchor="w",
        ).pack(side="left")

        if self.can_create_leases:
            ctk.CTkButton(
                header,
                text="+ New Lease",
                width=132,
                height=36,
                corner_radius=16,
                fg_color=self.SURFACE_SOFT,
                hover_color="#EEE7DA",
                text_color=self.TEXT,
                border_width=1,
                border_color="#D1C2AA",
                font=("Segoe UI", 13, "bold"),
                command=self._open_create_lease_modal,
            ).pack(side="right")

        filters = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        filters.pack(fill="x", padx=14, pady=(0, 10))
        self.filters_wrap = filters

        self.filter_buttons = {}
        for label in self.FILTERS:
            btn = ctk.CTkButton(
                filters,
                text=label,
                width=110 if len(label) < 11 else 128,
                height=34,
                corner_radius=17,
                command=lambda value=label: self._set_filter(value),
                font=("Segoe UI", 12, "bold"),
            )
            self.filter_buttons[label] = btn
        self._refresh_filter_buttons()

        self.list_area = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#DDCFB7",
            scrollbar_button_hover_color="#C9B696",
        )
        self.list_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_right_panel(self):
        self.right_scroll = ctk.CTkScrollableFrame(
            self.right_panel,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#DDCFB7",
            scrollbar_button_hover_color="#C9B696",
        )
        self.right_scroll.grid(row=0, column=0, sticky="nsew")

        self.detail_card = ctk.CTkFrame(
            self.right_scroll,
            fg_color=self.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER,
        )
        self.detail_card.pack(fill="x", pady=(0, 10))

        self.expiring_card = ctk.CTkFrame(
            self.right_scroll,
            fg_color=self.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER,
        )
        self.expiring_card.pack(fill="x", pady=(0, 10))

        self.notice_card = ctk.CTkFrame(
            self.right_scroll,
            fg_color=self.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER,
        )
        self.notice_card.pack(fill="x")

    def _set_filter(self, value):
        self.active_filter = value
        self._refresh_filter_buttons()
        self._apply_filters()

    def _refresh_filter_buttons(self):
        for label, button in self.filter_buttons.items():
            active = label == self.active_filter
            button.configure(
                fg_color=self.ACCENT if active else "#FFFFFF",
                hover_color=self.ACCENT_HOVER if active else "#F4ECDC",
                text_color="#FFFFFF" if active else "#6B5D44",
                border_width=1,
                border_color=self.ACCENT if active else "#D7C8AE",
            )
        self._layout_filter_buttons()

    def _layout_filter_buttons(self):
        width = max(self.filters_wrap.winfo_width(), 1)
        compact = self._is_compact or width < 980
        columns = 3 if compact else len(self.FILTERS)

        for idx in range(columns):
            self.filters_wrap.grid_columnconfigure(idx, weight=1 if compact else 0)

        for index, label in enumerate(self.FILTERS):
            button = self.filter_buttons[label]
            row = index // columns if compact else 0
            col = index % columns if compact else index
            button.grid(
                row=row,
                column=col,
                padx=(0, 8 if (not compact and index < len(self.FILTERS) - 1) else 0),
                pady=(0, 8 if compact else 0),
                sticky="ew" if compact else "",
            )

    def _on_layout_resize(self, event):
        width = int(event.width or 0)
        self._content_height = int(event.height or 0)
        compact = width < 1240
        stacked = width < 980

        if compact != self._is_compact or stacked != self._is_stacked:
            self._is_compact = compact
            self._is_stacked = stacked
            self._apply_responsive_layout()
            self._render_lease_rows()
            self._render_side_panels()

        self._layout_filter_buttons()

    def _apply_responsive_layout(self):
        self._layout_stat_cards()
        available_h = max(520, self._content_height - 116)

        if self._is_stacked:
            self.main.grid_columnconfigure(0, weight=1)
            self.main.grid_columnconfigure(1, weight=0)
            self.main.grid_rowconfigure(0, weight=0)
            self.main.grid_rowconfigure(1, weight=0)
            self.left_panel.configure(height=max(330, int(available_h * 0.56)))
            self.right_panel.configure(height=max(290, int(available_h * 0.44)))
            self.left_panel.grid_propagate(False)
            self.right_panel.grid_propagate(False)
            self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=(0, 10))
            self.right_panel.grid(row=1, column=0, sticky="nsew")
        else:
            self.main.grid_columnconfigure(0, weight=3)
            self.main.grid_columnconfigure(1, weight=2)
            self.main.grid_rowconfigure(0, weight=1)
            self.main.grid_rowconfigure(1, weight=0)
            self.left_panel.configure(height=available_h)
            self.right_panel.configure(height=available_h)
            self.left_panel.grid_propagate(False)
            self.right_panel.grid_propagate(False)
            self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
            self.right_panel.grid(row=0, column=1, sticky="nsew")

    def _layout_stat_cards(self):
        # Keep KPI cards in one row across all screen sizes.
        columns = 5
        for col in range(columns):
            self.stats_row.grid_columnconfigure(col, weight=1)

        for idx, key in enumerate(self.stat_order):
            card = self.stat_cards[key]
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0), pady=0)

    def _on_search_change(self, query):
        self.search_text = str(query or "").strip().lower()
        self._apply_filters()

    def _show_popup(self, title, message, kind="info"):
        palette = {
            "info": {"fg": self.TEXT, "btn": self.ACCENT, "hover": self.ACCENT_HOVER},
            "warning": {"fg": "#8B692A", "btn": "#D3B070", "hover": "#BE9C5E"},
            "error": {"fg": "#8E3030", "btn": "#D97575", "hover": "#C86464"},
            "success": {"fg": self.TEXT, "btn": "#D25590", "hover": "#BF4782"},
        }
        style = palette.get(kind, palette["info"])

        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("430x230")
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        self._center_popup(popup, 430, 230)

        wrap = ctk.CTkFrame(
            popup,
            fg_color="#FFFFFF",
            corner_radius=14,
            border_width=1,
            border_color=self.BORDER,
        )
        wrap.pack(fill="both", expand=True, padx=14, pady=14)

        if kind == "success":
            success_icon_path = os.path.join("images", "icons", "success.png")
            if Image is not None and os.path.exists(success_icon_path):
                try:
                    icon_img = ctk.CTkImage(light_image=Image.open(success_icon_path), size=(46, 46))
                    icon_label = ctk.CTkLabel(wrap, text="", image=icon_img)
                    icon_label.image = icon_img
                    icon_label.pack(pady=(12, 4))
                except Exception:
                    pass

        ctk.CTkLabel(
            wrap,
            text=title,
            text_color=style["fg"],
            font=("Georgia", 20, "bold"),
        ).pack(pady=(8 if kind == "success" else 18, 10))

        ctk.CTkLabel(
            wrap,
            text=str(message),
            text_color=self.TEXT,
            font=("Segoe UI", 12, "bold"),
            justify="center",
            wraplength=360,
        ).pack(padx=14, pady=(0, 16))

        ctk.CTkButton(
            wrap,
            text="OK",
            width=120,
            height=34,
            corner_radius=12,
            fg_color=style["btn"],
            hover_color=style["hover"],
            text_color="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            command=popup.destroy,
        ).pack()

    def _center_popup(self, win, width, height):
        host = self.winfo_toplevel()
        host.update_idletasks()
        x = host.winfo_rootx() + max((host.winfo_width() - width) // 2, 0)
        y = host.winfo_rooty() + max((host.winfo_height() - height) // 2, 0)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def _show_alerts(self):
        reminder_targets = [
            lease
            for lease in self.leases
            if lease["status_label"] in {"Active", "Expiring Soon", "Renewal Sent"}
            and 0 <= lease["days_left"] <= 60
        ]
        early_exit_count = sum(1 for lease in self.leases if lease["status_label"] == "Notice Given")
        expired_count = sum(1 for lease in self.leases if lease["status_label"] == "Expired")

        self.shell.show_premium_info_modal(
            title="Lease Alerts",
            icon_text="🔔",
            icon_fg="#B8891F",
            icon_bg="#F6E8B8",
            highlight_nonzero=True,
            rows=[
                ("Leases expiring in 60 days", str(len(reminder_targets))),
                ("Early-exit notices", str(early_exit_count)),
                ("Reminders already sent", str(len(self.sent_reminder_lease_ids))),
                ("Expired leases", str(expired_count)),
            ],
        )

    def _show_settings(self):
        user = AuthController.current_user

        def user_value(key, default=""):
            if user is None:
                return default
            try:
                return user[key]
            except Exception:
                pass
            try:
                return user.get(key, default)
            except Exception:
                return default

        role_key = str(user_value("role_name", self.role or "")).strip().lower()
        full_name = str(user_value("full_name", "Unknown User"))
        role_name = role_key.replace("_", " ").title() or "Unknown Role"
        location = str(user_value("location", self.city_scope or "Unknown"))
        is_admin = role_key == "admin"

        rows = [
            ("User", full_name),
            ("Role", role_name),
        ]
        if is_admin:
            rows.append(("Location Access", "Full location access (All Cities)"))
        else:
            rows.append(("Location", location))

        self.shell.show_premium_info_modal(
            title="Account Settings",
            icon_bg="#F6EED7",
            rows=rows,
            icon_image_name="settings",
            icon_image_size=(34, 34),
        )

    def load_tenants(self):
        tenants = TenantDAO.get_all_tenants()
        self.tenant_map = {f"{t['name']} (#{t['tenantID']})": t["tenantID"] for t in tenants}

    def load_available_apartments(self):
        apartments = ApartmentDAO.get_available_apartments(city=self.city_scope)
        self.apartment_map = {
            f"{apt['city']} · {apt['type']} (#{apt['apartmentID']})": apt["apartmentID"]
            for apt in apartments
        }

    def load_leases(self):
        LeaseDAO.expire_leases()
        rows = LeaseDAO.get_all_leases_with_financial_details(city=self.city_scope)
        self.leases = [self._lease_view_row(dict(row)) for row in rows]

        self.leases.sort(
            key=lambda lease: (
                1 if lease["status_label"] == "Expired" else 0,
                lease["days_left"],
            )
        )

        if self.selected_lease_id not in {lease["leaseID"] for lease in self.leases}:
            self.selected_lease_id = self.leases[0]["leaseID"] if self.leases else None

        self._update_metrics()
        self._apply_filters()
        self._render_side_panels()

    def _apply_filters(self):
        selected = self.active_filter
        query = self.search_text

        result = []
        for lease in self.leases:
            if selected != "All" and lease["status_label"] != selected:
                continue

            blob = " ".join(
                [
                    str(lease["leaseID"]),
                    lease["tenant_name"],
                    lease["apartment_type"],
                    str(lease["apartmentID"]),
                    lease["city"],
                    lease["status_label"],
                    lease["period"],
                ]
            ).lower()
            if query and query not in blob:
                continue
            result.append(lease)

        self.filtered_leases = result
        if self.selected_lease_id not in {lease["leaseID"] for lease in self.filtered_leases}:
            self.selected_lease_id = self.filtered_leases[0]["leaseID"] if self.filtered_leases else None

        self._render_lease_rows()
        self._render_side_panels()

    def _update_metrics(self):
        active = sum(1 for lease in self.leases if lease["status_label"] == "Active")
        expiring = sum(1 for lease in self.leases if lease["status_label"] == "Expiring Soon")
        notice = sum(1 for lease in self.leases if lease["status_label"] == "Notice Given")
        renewal = sum(1 for lease in self.leases if lease["status_label"] == "Renewal Sent")

        durations = [lease["duration_months"] for lease in self.leases if lease["duration_months"] > 0]
        avg_duration = round(sum(durations) / len(durations)) if durations else 0

        self.stat_values["ACTIVE LEASES"].configure(text=str(active))
        self.stat_values["EXPIRING IN 60 DAYS"].configure(text=str(expiring))
        self.stat_values["NOTICE GIVEN"].configure(text=str(notice))
        self.stat_values["UP FOR RENEWAL"].configure(text=str(renewal))
        self.stat_values["AVG LEASE LENGTH"].configure(text=f"{avg_duration} mo")

    def _render_lease_rows(self):
        for child in self.list_area.winfo_children():
            child.destroy()

        if not self.filtered_leases:
            ctk.CTkLabel(
                self.list_area,
                text="No leases match your current filters.",
                text_color=self.MUTED,
                font=("Segoe UI", 14),
            ).pack(fill="x", padx=8, pady=16)
            return

        for lease in self.filtered_leases:
            self._render_lease_row(lease)

    def _render_lease_row(self, lease):
        selected = lease["leaseID"] == self.selected_lease_id
        status_style = self.STATUS_STYLES[lease["status_label"]]
        border_color = self.ACCENT if selected else self.BORDER_SOFT
        card_height = 120

        card = ctk.CTkFrame(
            self.list_area,
            fg_color="#FFFDF9" if selected else self.CARD_TINT,
            corner_radius=14,
            border_width=1,
            border_color=border_color if selected else "#E8DDCB",
            height=card_height,
        )
        card.pack(fill="x", padx=4, pady=(0, 8))
        card.pack_propagate(False)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=12, pady=6)

        avatar = ctk.CTkFrame(
            row,
            fg_color="#EFE4CD",
            corner_radius=22,
            width=42,
            height=42,
            border_width=1,
            border_color="#D8C5A1",
        )
        avatar.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="n")
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=lease["initials"], text_color="#8D6A24", font=("Segoe UI", 12, "bold")).pack(expand=True)

        header = ctk.CTkFrame(row, fg_color="transparent")
        header.grid(row=0, column=1, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=lease["tenant_name"],
            text_color=self.TEXT,
            font=("Georgia", 13, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=lease["status_label"],
            text_color=status_style["fg"],
            fg_color=status_style["bg"],
            corner_radius=12,
            font=("Segoe UI", 9, "bold"),
            width=92,
            height=24,
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            header,
            text=f"{lease['unit_line']} · {lease['city']}",
            text_color=self.MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 0))

        summary = ctk.CTkFrame(row, fg_color="transparent")
        summary.grid(row=1, column=1, sticky="ew", pady=(2, 0))
        summary.grid_columnconfigure(0, weight=1)
        summary.grid_columnconfigure(1, weight=0)
        summary.grid_columnconfigure(2, weight=0)

        period_wrap = ctk.CTkFrame(summary, fg_color="transparent")
        period_wrap.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            period_wrap,
            text=lease["period"],
            text_color=self.TEXT,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            period_wrap,
            text=f"{lease['duration_months']} months",
            text_color=self.MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        days_color = status_style["fg"] if lease["days_left"] >= 0 else "#756954"
        ctk.CTkLabel(
            summary,
            text=f"{max(0, lease['days_left'])} days left",
            text_color=days_color,
            font=("Segoe UI", 9, "bold"),
            fg_color="#F4F0E8",
            corner_radius=10,
            height=22,
            width=100,
        ).grid(row=0, column=1, padx=(8, 8), sticky="e")

        ctk.CTkLabel(
            summary,
            text=f"£{lease['rent']:,.0f}/mo",
            text_color=self.TEXT,
            font=("Georgia", 12, "bold"),
        ).grid(row=0, column=2, sticky="e")

        row.grid_columnconfigure(1, weight=1)

        self._bind_click_recursive(card, lambda _event, lease_id=lease["leaseID"]: self._select_lease(lease_id))

    def _bind_click_recursive(self, widget, callback):
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click_recursive(child, callback)

    def _select_lease(self, lease_id):
        self.selected_lease_id = lease_id
        self._render_lease_rows()
        self._render_side_panels()

    def _selected_lease(self):
        for lease in self.leases:
            if lease["leaseID"] == self.selected_lease_id:
                return lease
        return None

    def _render_side_panels(self):
        self._render_detail_panel()
        self._render_expiring_panel()
        self._render_notice_panel()

    def _render_detail_panel(self):
        for child in self.detail_card.winfo_children():
            child.destroy()

        selected = self._selected_lease()
        if not selected:
            ctk.CTkLabel(
                self.detail_card,
                text="Select a lease to view details.",
                text_color=self.MUTED,
                font=("Segoe UI", 13),
            ).pack(pady=16)
            return

        status_style = self.STATUS_STYLES[selected["status_label"]]

        head = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(12, 8))

        avatar = ctk.CTkFrame(head, fg_color="#EFE4CD", corner_radius=22, width=44, height=44)
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=selected["initials"], text_color="#8D6A24", font=("Segoe UI", 12, "bold")).pack(expand=True)

        text_wrap = ctk.CTkFrame(head, fg_color="transparent")
        text_wrap.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(text_wrap, text=selected["tenant_name"], text_color=self.TEXT, font=("Georgia", 21, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(
            text_wrap,
            text=f"{selected['unit_line']} · {selected['city']}",
            text_color=self.MUTED,
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            head,
            text=selected["status_label"],
            text_color=status_style["fg"],
            fg_color=status_style["bg"],
            corner_radius=12,
            font=("Segoe UI", 10, "bold"),
            width=92,
            height=27,
        ).pack(side="right")

        ctk.CTkFrame(self.detail_card, fg_color="#EEE6D7", height=1).pack(fill="x", padx=12, pady=(0, 8))

        details = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        details.pack(fill="x", padx=14)

        rows = [
            ("Lease ID", f"#{selected['leaseID']}"),
            ("Lease Start", self._format_date(selected["start_date"])),
            ("Lease End", self._format_date(selected["end_date"])),
            ("Duration", f"{selected['duration_months']} months"),
            ("Monthly Rent", f"£{selected['rent']:,.2f}"),
            ("Progress", f"{selected['progress_pct']}% elapsed"),
        ]

        for left, right in rows:
            row = ctk.CTkFrame(details, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=left, text_color=self.LABEL, font=("Segoe UI", 11, "bold")).pack(side="left")
            ctk.CTkLabel(row, text=right, text_color=self.TEXT, font=("Segoe UI", 11, "bold")).pack(side="right")

        timeline = ctk.CTkFrame(self.detail_card, fg_color="#F6F2EA", corner_radius=12, border_width=1, border_color="#E1D5C2")
        timeline.pack(fill="x", padx=14, pady=(10, 10))

        timeline_title = f"{max(0, selected['days_left'])} days until lease ends"
        timeline_subtitle = f"Ends {self._format_date(selected['end_date'])}"
        if selected["status_label"] == "Expired":
            timeline_title = "Lease has ended"
            timeline_subtitle = f"Ended {self._format_date(selected['end_date'])}"
        elif selected["status_label"] == "Notice Given":
            timeline_title = "Early exit in progress"
            timeline_subtitle = f"Vacating {self._format_date(selected['end_date'])}"

        ctk.CTkLabel(
            timeline,
            text=timeline_title,
            text_color=status_style["fg"],
            font=("Georgia", 26, "bold"),
        ).pack(pady=(10, 0))
        ctk.CTkLabel(
            timeline,
            text=timeline_subtitle,
            text_color=self.MUTED,
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(0, 10))

        actions = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        actions.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(
            actions,
            text="Renew Lease",
            height=34,
            corner_radius=12,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 11, "bold"),
            command=self._open_renew_lease_modal,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            actions,
            text="Print PDF",
            height=34,
            corner_radius=12,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 11, "bold"),
            command=self._export_selected_lease_pdf,
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

        ctk.CTkButton(
            self.detail_card,
            text="End Early",
            height=34,
            corner_radius=12,
            fg_color="#F5E7E7",
            hover_color="#EFD7D7",
            text_color="#8E3030",
            border_width=1,
            border_color="#DFC0C0",
            font=("Segoe UI", 11, "bold"),
            command=self.terminate_lease,
        ).pack(fill="x", padx=14, pady=(0, 14))

    def _render_expiring_panel(self):
        for child in self.expiring_card.winfo_children():
            child.destroy()

        head = ctk.CTkFrame(self.expiring_card, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(head, text="Expiring Within 60 Days", text_color=self.TEXT, font=("Segoe UI", 13, "bold")).pack(side="left")
        ctk.CTkButton(
            head,
            text="Send all reminders",
            width=154,
            height=28,
            corner_radius=12,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color="#8B692A",
            border_width=1,
            border_color="#D4C3A6",
            font=("Segoe UI", 11, "bold"),
            command=self._send_all_reminders,
        ).pack(side="right")

        reminder_statuses = {"Active", "Expiring Soon", "Renewal Sent"}
        expiring = [
            lease
            for lease in self.leases
            if lease["status_label"] in reminder_statuses and 0 <= lease["days_left"] <= 60
        ]
        if not expiring:
            ctk.CTkLabel(
                self.expiring_card,
                text="No leases expiring in the next 60 days.",
                text_color=self.MUTED,
                font=("Segoe UI", 11),
            ).pack(fill="x", padx=14, pady=(0, 10))
            return

        for lease in expiring[:4]:
            row = ctk.CTkFrame(self.expiring_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(0, 8))

            ctk.CTkLabel(
                row,
                text=lease["initials"],
                text_color="#8E3030" if lease["days_left"] <= 14 else "#8B692A",
                fg_color="#F3DDDD" if lease["days_left"] <= 14 else "#F4E8CF",
                corner_radius=14,
                width=34,
                height=28,
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")

            text_wrap = ctk.CTkFrame(row, fg_color="transparent")
            text_wrap.pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkLabel(
                text_wrap,
                text=f"{lease['tenant_name']} · Unit #{lease['apartmentID']}",
                text_color=self.TEXT,
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            ).pack(fill="x")
            ctk.CTkLabel(
                text_wrap,
                text=f"Ends {self._format_date(lease['end_date'])}",
                text_color=self.MUTED,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                row,
                text=(
                    "Reminder Sent"
                    if lease["leaseID"] in self.sent_reminder_lease_ids
                    else f"{max(0, lease['days_left'])} days"
                ),
                text_color="#8E3030" if lease["days_left"] <= 14 else "#8B692A",
                fg_color="#F3DDDD" if lease["days_left"] <= 14 else "#F4E8CF",
                corner_radius=12,
                width=118 if lease["leaseID"] in self.sent_reminder_lease_ids else 74,
                height=25,
                font=("Segoe UI", 10, "bold"),
            ).pack(side="right")

    def _send_all_reminders(self):
        reminder_statuses = {"Active", "Expiring Soon", "Renewal Sent"}
        expiring = [
            lease
            for lease in self.leases
            if lease["status_label"] in reminder_statuses and 0 <= lease["days_left"] <= 60
        ]
        if not expiring:
            self._show_popup("No Reminders", "There are no leases expiring within 60 days.", "info")
            return

        reminder_count = 0
        already_sent = 0
        for lease in expiring:
            lease_id = lease["leaseID"]
            if lease_id in self.sent_reminder_lease_ids:
                already_sent += 1
                continue
            self.sent_reminder_lease_ids.add(lease_id)
            reminder_count += 1

        if reminder_count == 0:
            self._show_popup(
                "Reminders Up To Date",
                f"All {already_sent} expiring leases already have reminders marked as sent.",
                "info",
            )
            return

        self._render_expiring_panel()
        self._show_popup(
            "Reminders Sent",
            f"Sent reminders for {reminder_count} lease(s) expiring within 60 days.",
            "success",
        )

    def _render_notice_panel(self):
        for child in self.notice_card.winfo_children():
            child.destroy()

        notices = [lease for lease in self.leases if lease["status_label"] == "Notice Given"]

        head = ctk.CTkFrame(self.notice_card, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(head, text="Early Exit Notices", text_color=self.TEXT, font=("Segoe UI", 13, "bold")).pack(side="left")
        ctk.CTkLabel(head, text=f"{len(notices)} active", text_color="#8B692A", font=("Segoe UI", 12, "bold")).pack(side="right")

        if not notices:
            ctk.CTkLabel(
                self.notice_card,
                text="No early-exit notices at the moment.",
                text_color=self.MUTED,
                font=("Segoe UI", 11),
            ).pack(fill="x", padx=14, pady=(0, 10))
            return

        for lease in notices[:3]:
            penalty = lease["rent"] * 0.05
            row = ctk.CTkFrame(self.notice_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(0, 8))

            ctk.CTkLabel(
                row,
                text="!!",
                text_color="#8E3030",
                fg_color="#F3DDDD",
                corner_radius=14,
                width=32,
                height=28,
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")

            text_wrap = ctk.CTkFrame(row, fg_color="transparent")
            text_wrap.pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkLabel(text_wrap, text=f"{lease['tenant_name']} · Unit #{lease['apartmentID']}", text_color=self.TEXT, font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(text_wrap, text=f"Vacating {self._format_date(lease['end_date'])}", text_color=self.MUTED, font=("Segoe UI", 10), anchor="w").pack(fill="x")
            ctk.CTkLabel(
                text_wrap,
                text=f"Penalty: £{penalty:.2f} (5% of £{lease['rent']:,.0f})",
                text_color="#8E3030",
                font=("Segoe UI", 10, "bold"),
                anchor="w",
            ).pack(fill="x")

    def terminate_lease(self):
        selected = self._selected_lease()
        if not selected:
            self._show_popup("Error", "Please select a lease first.", "error")
            return

        if selected["status_label"] == "Expired":
            self._show_popup("Lease Ended", "This lease is already ended.", "info")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Terminate Lease")
        popup.geometry("430x290")
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        wrap = ctk.CTkFrame(popup, fg_color="#FFFFFF", corner_radius=14, border_width=1, border_color=self.BORDER)
        wrap.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(wrap, text="Terminate Lease", text_color=self.TEXT, font=("Georgia", 22, "bold")).pack(pady=(14, 4))
        ctk.CTkLabel(
            wrap,
            text=f"{selected['tenant_name']} · Unit #{selected['apartmentID']}",
            text_color=self.MUTED,
            font=("Segoe UI", 12),
        ).pack()

        ctk.CTkLabel(
            wrap,
            text="Early termination applies a 5% monthly-rent penalty\nif the lease has not reached end date.",
            text_color="#8E3030",
            font=("Segoe UI", 11, "bold"),
            justify="center",
        ).pack(pady=(14, 18))

        actions = ctk.CTkFrame(wrap, fg_color="transparent")
        actions.pack()

        ctk.CTkButton(
            actions,
            text="Cancel",
            width=120,
            height=36,
            corner_radius=12,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 12, "bold"),
            command=popup.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions,
            text="Confirm Termination",
            width=180,
            height=36,
            corner_radius=12,
            fg_color="#E58C8C",
            hover_color="#D97575",
            text_color="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            command=lambda: self._confirm_termination(selected, popup),
        ).pack(side="left")

    def _confirm_termination(self, selected, popup):
        penalty = LeaseDAO.terminate_lease(selected["leaseID"])
        popup.destroy()
        self._show_termination_record(selected, penalty)
        self.load_available_apartments()
        self.load_leases()

    def _show_termination_record(self, selected, penalty):
        record = ctk.CTkToplevel(self)
        record.title("Lease Termination Record")
        record.geometry("560x500")
        record.resizable(False, False)
        record.transient(self.winfo_toplevel())
        record.grab_set()
        self._center_popup(record, 560, 500)

        card = ctk.CTkFrame(record, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color=self.BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(card, text="Lease Termination Record", text_color=self.TEXT, font=("Georgia", 22, "bold")).pack(pady=(14, 8))

        lines = [
            f"Lease ID: #{selected['leaseID']}",
            f"Tenant: {selected['tenant_name']}",
            f"Apartment: Unit #{selected['apartmentID']} ({selected['apartment_type']})",
            f"Start Date: {self._format_date(selected['start_date'])}",
            f"Original End Date: {self._format_date(selected['end_date'])}",
            f"Termination Date: {date.today().isoformat()}",
            f"Penalty Charged: £{penalty:.2f}",
        ]

        for line in lines:
            ctk.CTkLabel(card, text=line, text_color=self.TEXT, font=("Segoe UI", 12), anchor="w").pack(fill="x", padx=20, pady=1)

        status_text = "Early Termination" if penalty > 0 else "Contract Completed"
        ctk.CTkLabel(
            card,
            text=f"Termination Type: {status_text}",
            text_color="#8E3030" if penalty > 0 else "#2F6B3F",
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(14, 14))

        ctk.CTkButton(
            card,
            text="Close",
            width=120,
            height=36,
            corner_radius=12,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            command=record.destroy,
        ).pack(pady=(0, 18))

    def _open_create_lease_modal(self):
        if not self.can_create_leases:
            self._show_popup("Read-only Access", "Your role can view leases but cannot create new leases.", "warning")
            return
        self.load_tenants()
        self.load_available_apartments()

        if not self.tenant_map:
            self._show_popup("No Tenants", "Please register a tenant first.", "warning")
            return
        if not self.apartment_map:
            self._show_popup("No Apartments", "No available apartments in your current city scope.", "warning")
            return

        modal = ctk.CTkToplevel(self)
        modal.title("Create Lease")
        modal.geometry("520x430")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        wrap = ctk.CTkFrame(modal, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color=self.BORDER)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(wrap, text="Create New Lease", text_color=self.TEXT, font=("Georgia", 24, "bold")).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(wrap, text="Assign tenant, unit, and lease dates.", text_color=self.MUTED, font=("Segoe UI", 11)).pack(anchor="w", padx=18, pady=(0, 10))

        form = ctk.CTkFrame(wrap, fg_color="#F8F4EC", corner_radius=12, border_width=1, border_color="#E3D9C8")
        form.pack(fill="x", padx=16, pady=(0, 12))

        for i in range(2):
            form.grid_columnconfigure(i, weight=1)

        ttk.Style(modal).configure("LeaseCreate.TCombobox", padding=6)

        ttk.Label(form, text="Tenant", background="#F8F4EC", foreground=self.LABEL).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        tenant_combo = ttk.Combobox(form, state="readonly", values=list(self.tenant_map.keys()), style="LeaseCreate.TCombobox")
        tenant_combo.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        tenant_combo.current(0)

        ttk.Label(form, text="Apartment", background="#F8F4EC", foreground=self.LABEL).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 2))
        apartment_combo = ttk.Combobox(form, state="readonly", values=list(self.apartment_map.keys()), style="LeaseCreate.TCombobox")
        apartment_combo.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 8))
        apartment_combo.current(0)

        start_var = tk.StringVar(value=date.today().isoformat())
        end_var = tk.StringVar(value=(date.today() + timedelta(days=365)).isoformat())

        ttk.Label(form, text="Start Date", background="#F8F4EC", foreground=self.LABEL).grid(
            row=2, column=0, sticky="w", padx=10, pady=(4, 2)
        )
        start_wrap = ctk.CTkFrame(form, fg_color="transparent")
        start_wrap.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 8))
        start_wrap.grid_columnconfigure(0, weight=1)
        ttk.Entry(start_wrap, textvariable=start_var).grid(row=0, column=0, sticky="ew")

        def pick_start_date():
            self._open_calendar_picker(modal, start_var)
            start_d = self._to_date(start_var.get()) or date.today()
            end_d = self._to_date(end_var.get()) or (start_d + timedelta(days=365))
            if end_d <= start_d:
                end_var.set((start_d + timedelta(days=365)).isoformat())

        ctk.CTkButton(
            start_wrap,
            text="Pick",
            width=54,
            height=28,
            corner_radius=8,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 10, "bold"),
            command=pick_start_date,
        ).grid(row=0, column=1, padx=(8, 0))

        ttk.Label(form, text="End Date", background="#F8F4EC", foreground=self.LABEL).grid(
            row=2, column=1, sticky="w", padx=10, pady=(4, 2)
        )
        end_wrap = ctk.CTkFrame(form, fg_color="transparent")
        end_wrap.grid(row=3, column=1, sticky="ew", padx=10, pady=(0, 8))
        end_wrap.grid_columnconfigure(0, weight=1)
        ttk.Entry(end_wrap, textvariable=end_var).grid(row=0, column=0, sticky="ew")

        def pick_end_date():
            min_date = self._to_date(start_var.get()) or date.today()
            self._open_calendar_picker(modal, end_var, min_date=min_date)

        ctk.CTkButton(
            end_wrap,
            text="Pick",
            width=54,
            height=28,
            corner_radius=8,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 10, "bold"),
            command=pick_end_date,
        ).grid(row=0, column=1, padx=(8, 0))

        actions = ctk.CTkFrame(wrap, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=(4, 14))

        ctk.CTkButton(
            actions,
            text="Cancel",
            width=110,
            height=36,
            corner_radius=12,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 12, "bold"),
            command=modal.destroy,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text="Create Lease",
            width=140,
            height=36,
            corner_radius=12,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            command=lambda: self._submit_create_lease(
                modal,
                tenant_combo.get(),
                apartment_combo.get(),
                start_var.get(),
                end_var.get(),
            ),
        ).pack(side="right")

    def _submit_create_lease(self, modal, tenant_display, apartment_display, start_date, end_date):
        if not self.can_create_leases:
            self._show_popup("Read-only Access", "Your role can view leases but cannot create new leases.", "warning")
            return
        tenant_id = self.tenant_map.get(tenant_display)
        apartment_id = self.apartment_map.get(apartment_display)

        if not tenant_id or not apartment_id:
            self._show_popup("Invalid Selection", "Please select tenant and apartment.", "warning")
            return

        result = LeaseController.create_lease(tenant_id, apartment_id, start_date, end_date)
        if result != "Success":
            self._show_popup("Create Lease Failed", result, "error")
            return

        modal.destroy()
        self._show_popup("Lease Created", "Lease created successfully.", "success")
        self.load_available_apartments()
        self.load_leases()

    def _open_renew_lease_modal(self):
        selected = self._selected_lease()
        if not selected:
            self._show_popup("Error", "Please select a lease first.", "error")
            return

        modal = ctk.CTkToplevel(self)
        modal.title("Renew Lease")
        modal.geometry("480x320")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        wrap = ctk.CTkFrame(modal, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color=self.BORDER)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            wrap,
            text="Renew Lease",
            text_color=self.TEXT,
            font=("Georgia", 24, "bold"),
        ).pack(anchor="w", padx=18, pady=(14, 2))

        ctk.CTkLabel(
            wrap,
            text=f"{selected['tenant_name']} · Unit #{selected['apartmentID']}",
            text_color=self.MUTED,
            font=("Segoe UI", 12),
        ).pack(anchor="w", padx=18, pady=(0, 10))

        form = ctk.CTkFrame(
            wrap,
            fg_color="#F8F4EC",
            corner_radius=12,
            border_width=1,
            border_color="#E3D9C8",
        )
        form.pack(fill="x", padx=16, pady=(0, 12))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        ttk.Label(form, text="Current End Date", background="#F8F4EC", foreground=self.LABEL).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 2)
        )
        ttk.Label(form, text=self._format_date(selected["end_date"]), background="#F8F4EC", foreground=self.TEXT).grid(
            row=1, column=0, sticky="w", padx=10, pady=(0, 8)
        )

        ttk.Label(form, text="New End Date", background="#F8F4EC", foreground=self.LABEL).grid(
            row=0, column=1, sticky="w", padx=10, pady=(10, 2)
        )
        current_end = self._to_date(selected["end_date"]) or date.today()
        suggested_end = current_end + timedelta(days=365)
        new_end_var = tk.StringVar(value=suggested_end.isoformat())

        renew_wrap = ctk.CTkFrame(form, fg_color="transparent")
        renew_wrap.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 8))
        renew_wrap.grid_columnconfigure(0, weight=1)
        ttk.Entry(renew_wrap, textvariable=new_end_var).grid(row=0, column=0, sticky="ew")

        ctk.CTkButton(
            renew_wrap,
            text="Pick",
            width=54,
            height=28,
            corner_radius=8,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 10, "bold"),
            command=lambda: self._open_calendar_picker(
                modal,
                new_end_var,
                min_date=current_end + timedelta(days=1),
            ),
        ).grid(row=0, column=1, padx=(8, 0))

        actions = ctk.CTkFrame(wrap, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=(4, 14))

        ctk.CTkButton(
            actions,
            text="Cancel",
            width=110,
            height=36,
            corner_radius=12,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CBBCA5",
            font=("Segoe UI", 12, "bold"),
            command=modal.destroy,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text="Confirm Renewal",
            width=160,
            height=36,
            corner_radius=12,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            command=lambda: self._submit_renew_lease(
                modal,
                selected,
                new_end_var.get(),
            ),
        ).pack(side="right")

    def _submit_renew_lease(self, modal, selected, new_end_date):
        result = LeaseController.renew_lease(selected["leaseID"], new_end_date)
        if result != "Success":
            self._show_popup("Renewal Failed", result, "error")
            return

        modal.destroy()
        self._show_popup("Lease Renewed", "Lease end date updated successfully.", "success")
        self.load_leases()

    def _export_selected_lease_pdf(self):
        selected = self._selected_lease()
        if not selected:
            self._show_popup("No Selection", "Please select a lease first.", "warning")
            return

        try:
            from fpdf import FPDF
        except ImportError:
            self._show_popup(
                "Missing Package",
                "PDF export needs fpdf2.\n\nInstall it with:\npip install fpdf2",
                "error",
            )
            return

        default_name = f"lease_{selected['leaseID']}_{selected['tenant_name'].replace(' ', '_').lower()}.pdf"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title="Save Lease Summary PDF",
        )
        if not path:
            return

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Lease Summary #{selected['leaseID']}", ln=True)

        pdf.set_font("Arial", size=11)
        lines = [
            f"Tenant: {selected['tenant_name']}",
            f"Apartment: Unit #{selected['apartmentID']} ({selected['apartment_type']})",
            f"City: {selected.get('city', 'Unknown')}",
            "",
            f"Status: {selected['status_label']}",
            f"Lease Period: {selected['period']}",
            f"Start Date: {selected['start_date']}",
            f"End Date: {selected['end_date']}",
            f"Duration: {selected['duration_months']} months",
            f"Days Remaining: {max(0, selected['days_left'])}",
            f"Progress: {selected['progress_pct']}% elapsed",
            f"Monthly Rent: GBP {selected['rent']:,.2f}",
            "",
            f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        for line in lines:
            pdf.cell(0, 8, line, ln=True)

        pdf.output(path)
        self._show_popup("Export Complete", f"Lease PDF saved to:\n{path}", "success")
