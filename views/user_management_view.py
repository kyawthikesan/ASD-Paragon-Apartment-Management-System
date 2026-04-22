# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

import customtkinter as ctk

from controllers.auth_controller import AuthController
from dao.user_dao import UserDAO
from views.premium_shell import PremiumAppShell

# Pillow is optional and is only used for loading custom icons.
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    Image = None
    PIL_AVAILABLE = False


class UserManagementView(ctk.CTkFrame):
    """
    User management screen for administrators.

    This view allows staff to:
    - view all users
    - search users
    - activate/deactivate accounts
    - add and edit users
    - manage role-based permissions
    """

    # Controls the display order of roles across the UI.
    ROLE_ORDER = ["admin", "finance", "front_desk", "maintenance", "manager"]

    # Human-readable labels used in pills, tables, and forms.
    ROLE_LABELS = {
        "admin": "Administrator",
        "finance": "Finance Manager",
        "front_desk": "Front-Desk Staff",
        "maintenance": "Maintenance Staff",
        "manager": "Manager",
    }

    # Plural role labels used in summary cards.
    ROLE_CARD_LABELS = {
        "admin": "Administrators",
        "finance": "Finance Managers",
        "front_desk": "Front-Desk Staff",
        "maintenance": "Maintenance Staff",
        "manager": "Managers",
    }

    # Role-specific colour themes for badges and role styling.
    ROLE_COLORS = {
        "admin": ("#E8F0FA", "#1A4A7A"),
        "finance": ("#EAF3EA", "#3B6D3B"),
        "front_desk": ("#EDE8DC", "#6B5D44"),
        "maintenance": ("#FDF3DC", "#7A5A0A"),
        "manager": ("#EEEDFE", "#3C3489"),
    }

    # Predefined locations available when creating or editing a user.
    LOCATION_VALUES = ["Bristol", "Cardiff", "London", "Manchester"]

    # Permissions shown in the role-permission matrix.
    PERMISSION_ROWS = [
        ("register_tenants", "Register Tenants"),
        ("manage_payments", "Manage Payments"),
        ("log_maintenance", "Log Maintenance"),
        ("generate_reports", "Generate Reports"),
        ("manage_user_accounts", "Manage User Accounts"),
    ]

    def __init__(self, parent, go_back, open_apartment_management=None):
        super().__init__(parent, fg_color="#F8F5F0")
        self.go_back = go_back
        self.open_apartment_management = open_apartment_management or go_back

        # Tracks current selection and cached user/permission data.
        self.selected_user_id = None
        self._users = []
        self._search_query = ""
        self._row_cards = {}
        self._permissions_matrix = {}
        self._role_icon_cache = {}
        self._role_cards = []
        self._users_header_labels = []

        # Used to avoid excessive redraws during resize and search polling.
        self._responsive_job = None
        self._responsive_key = None
        self._search_watch_job = None
        self._last_search_value = ""

        # Responsive layout defaults for fonts, paddings and element sizes.
        self._permissions_header_font_size = 11
        self._permissions_row_font_size = 13
        self._permissions_mark_font_size = 14
        self._row_height = 66
        self._avatar_size = 28
        self._avatar_font_size = 10
        self._user_cell_left_pad = 8
        self._user_avatar_gap = 6
        self._name_font_size = 12
        self._meta_font_size = 11
        self._pill_font_size = 11
        self._pill_height = 24
        self._role_pill_width = 150
        self._status_width = 88
        self._user_col_weights = (3, 3, 2, 2, 2)
        self._permissions_col_weights = (2, 1, 1, 1, 1, 1)
        self._user_name_max_chars = 28
        self._scrollbar_gutter = 18

        # Read logged-in user details so the screen can adapt based on access.
        self.current_user = AuthController.current_user
        self.role = self._row_value(self.current_user, "role_name", "")
        self.full_name = self._row_value(self.current_user, "full_name", "User")
        self.location = self._row_value(self.current_user, "location", "All Cities")

        self.pack(fill="both", expand=True)

        # Build sidebar navigation dynamically based on what the current user
        # is allowed to access.
        management_items = []
        if AuthController.can_access_feature("tenant_management"):
            management_items.append({"label": "Tenants", "action": self.go_back, "icon": "tenants"})
        if AuthController.can_access_feature("apartment_management"):
            management_items.append(
                {
                    "label": "Apartments",
                    "action": self.open_apartment_management,
                    "icon": "apartments",
                }
            )
        if AuthController.can_access_feature("lease_management"):
            management_items.append({"label": "Leases", "action": self.go_back, "icon": "leases"})
        if AuthController.can_access_feature("maintenance_dashboard"):
            management_items.append({"label": "Maintenance", "action": self.go_back, "icon": "openissues"})

        finance_items = []
        if AuthController.can_access_feature("payment_management"):
            finance_items.append({"label": "Payments", "action": self.go_back, "icon": "payments"})
        if AuthController.can_access_feature("reports"):
            finance_items.append({"label": "Reports", "action": self.go_back, "icon": "reports"})

        # Shared premium shell provides common layout structure and header tools.
        self.shell = PremiumAppShell(
            self,
            page_title="User Access Control",
            on_logout=self.go_back,
            active_nav="User Access",
            nav_sections=[
                {"title": "Overview", "items": [{"label": "Dashboard", "action": self.go_back, "icon": "dashboard"}]},
                {"title": "Management", "items": management_items},
                {"title": "Finance", "items": finance_items},
                {"title": "Admin", "items": [{"label": "User Access", "action": lambda: None, "icon": "shield"}]},
            ],
            footer_action_label="Back to Dashboard",
            search_placeholder="Search users...",
            on_search_change=self._on_search_change,
            on_search_submit=self._on_search_change,
            on_bell_click=self._show_alerts,
            on_settings_click=self._show_settings,
            notification_count=self._initial_notification_count(),
        )

        # Main content area contains:
        # row 0 = summary cards
        # row 1 = users table
        # row 2 = permissions matrix
        content = self.shell.content
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=0)
        content.grid_rowconfigure(1, weight=1)
        content.grid_rowconfigure(2, weight=0)

        self._build_role_cards(content)
        self._build_users_panel(content)
        self._build_permissions_panel(content)
        self._bind_search_handlers()

        # Initial data load and responsive layout setup.
        self.load_users()
        self.bind("<Configure>", self._on_resized)
        self.after(120, self._apply_responsive_layout)

    @staticmethod
    def _row_value(row, key, default=""):
        """Safely read a value from a database row-like object."""
        try:
            return row[key]
        except Exception:
            return default

    def _bind_search_handlers(self):
        """Search events are already handled by PremiumAppShell callbacks."""
        return

    def _start_search_watch(self):
        """Starts a lightweight polling loop to detect programmatic search changes."""
        if self._search_watch_job:
            try:
                self.after_cancel(self._search_watch_job)
            except Exception:
                pass
        self._search_watch_job = self.after(150, self._poll_search_entry)

    def _poll_search_entry(self):
        """Keeps search state in sync with the visible search box."""
        self._search_watch_job = None
        try:
            entry = getattr(self.shell, "search_entry", None)
            if not entry or not entry.winfo_exists():
                return
            current_value = (entry.get() or "").strip()
            if current_value != self._last_search_value:
                self._last_search_value = current_value
                self._on_search_change(current_value)
        except Exception:
            return
        self._search_watch_job = self.after(150, self._poll_search_entry)

    def _initial_notification_count(self):
        """Shows number of inactive users as the initial notification count."""
        try:
            rows = UserDAO.get_all_users()
            return sum(1 for row in rows if int(row.get("is_active", 0)) != 1)
        except Exception:
            return 0

    def _build_role_cards(self, parent):
        """Create top summary cards showing number of users in each role."""
        wrap = ctk.CTkFrame(parent, fg_color="#F8F5F0", corner_radius=0)
        wrap.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._summary_labels = {}
        self._role_cards_wrap = wrap
        self._role_cards = []

        cards = [
            ("admin", "admin", "Full location access"),
            ("finance", "finance", "Payments & reports"),
            ("front_desk", "frontdesk", "Tenants & inquiries"),
            ("maintenance", "maintenance", "Issue management"),
            ("manager", "manager", "All cities oversight"),
        ]

        for idx, (key, icon_key, note) in enumerate(cards):
            card = ctk.CTkFrame(
                wrap,
                fg_color="#F3EFE7",
                corner_radius=12,
                border_width=1,
                border_color="#D8CAB0",
                height=92,
            )
            card.grid(row=0, column=idx, sticky="ew", padx=5, pady=0)
            card.grid_propagate(False)
            card.grid_columnconfigure(0, weight=1)

            title_row = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0, height=22)
            title_row.pack(fill="x", padx=8, pady=(6, 1))
            title_row.pack_propagate(False)

            # Load an optional icon for the role card.
            icon_image = self._load_role_icon(icon_key, size=(15, 15))
            if icon_image:
                icon_label = ctk.CTkLabel(title_row, text="", image=icon_image, fg_color="transparent")
                icon_label.pack(side="left", padx=(0, 5))
                icon_label._icon_ref = icon_image

            title_lbl = ctk.CTkLabel(
                title_row,
                text=self.ROLE_CARD_LABELS[key],
                font=("Arial", 11, "bold"),
                text_color="#2C2416",
                justify="left",
                anchor="w",
            )
            title_lbl.pack(side="left", fill="x", expand=True)

            count_lbl = ctk.CTkLabel(
                card,
                text="0",
                font=("Georgia", 18, "bold"),
                text_color="#9A7A2E",
            )
            count_lbl.pack(pady=(0, 0))
            self._summary_labels[key] = count_lbl

            note_lbl = ctk.CTkLabel(
                card,
                text=note,
                font=("Arial", 10),
                text_color="#9E8F77"
            )
            note_lbl.pack(pady=(0, 5))

            self._role_cards.append({
                "card": card,
                "title": title_lbl,
                "count": count_lbl,
                "note": note_lbl
            })

    def _load_role_icon(self, icon_key, size=(18, 18)):
        """Loads and caches role icons to avoid reopening image files repeatedly."""
        cache_key = (icon_key, size)
        cached = self._role_icon_cache.get(cache_key)
        if cached:
            return cached

        icon_path = os.path.join("images", "icons", f"{icon_key}.png")
        if not os.path.exists(icon_path) or not PIL_AVAILABLE:
            return None

        try:
            image = Image.open(icon_path).convert("RGBA")
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)
            self._role_icon_cache[cache_key] = ctk_image
            return ctk_image
        except Exception:
            return None

    def _build_users_panel(self, parent):
        """Builds the main user table area and action buttons."""
        panel = ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=22,
            border_width=1,
            border_color="#E3D9C9",
            height=500,
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        self._users_panel = panel

        top = ctk.CTkFrame(panel, fg_color="#FFFFFF", corner_radius=0, height=64)
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(8, 0))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)
        top.grid_propagate(False)
        self._users_top = top

        self._users_title_label = ctk.CTkLabel(
            top,
            text="All Users",
            font=("Arial", 20, "bold"),
            text_color="#2C2416",
        )
        self._users_title_label.grid(row=0, column=0, sticky="w")

        self._users_actions = ctk.CTkFrame(top, fg_color="transparent", corner_radius=0)
        self._users_actions.grid(row=0, column=1, sticky="e")

        # Main actions for user administration.
        self._add_user_btn = ctk.CTkButton(
            self._users_actions,
            text="+ Add User",
            command=lambda: self._open_user_modal(),
            fg_color="#1C170F",
            hover_color="#2B2417",
            text_color="#C9A84C",
            border_width=1,
            border_color="#6B5624",
            corner_radius=14,
            width=155,
            height=40,
            font=("Arial", 13, "bold"),
        )
        self._add_user_btn.grid(row=0, column=0)

        self._update_user_btn = ctk.CTkButton(
            self._users_actions,
            text="Update",
            command=self._open_selected_for_edit,
            fg_color="#EEE7D9",
            hover_color="#E2D8C6",
            text_color="#2C2416",
            corner_radius=14,
            width=130,
            height=40,
            font=("Arial", 13, "bold"),
            state="disabled",
        )
        self._update_user_btn.grid(row=0, column=1, padx=(10, 0))

        self._toggle_active_btn = ctk.CTkButton(
            self._users_actions,
            text="Deactivate",
            command=self._toggle_selected_user_active,
            fg_color="#EEE7D9",
            hover_color="#E2D8C6",
            text_color="#9F1D1D",
            corner_radius=14,
            width=150,
            height=40,
            font=("Arial", 13, "bold"),
            state="disabled",
        )
        self._toggle_active_btn.grid(row=0, column=2, padx=(10, 0))

        body = ctk.CTkFrame(panel, fg_color="#FFFFFF", corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew", padx=20, pady=(4, 10))
        body.grid_rowconfigure(2, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self._users_body = body

        # Column header for the users table.
        header = ctk.CTkFrame(body, fg_color="#FFFFFF", corner_radius=0, height=32)
        header.grid(row=0, column=0, sticky="ew", padx=(0, self._scrollbar_gutter))
        header.grid_propagate(False)
        self._users_header = header
        self._set_users_header_column_weights(self._user_col_weights)

        header_labels = ("USER", "ROLE", "LOCATION", "LAST LOGIN", "STATUS")
        header_colors = ("#9E8F77", "#1A4A7A", "#6B5D44", "#8B7F6B", "#3B6D3B")

        self._users_header_labels = []
        for idx, (text, color) in enumerate(zip(header_labels, header_colors)):
            if idx == 0:
                # USER header is padded so it aligns with the user name text,
                # not the avatar circle.
                column_anchor = "w"
                column_padx = (self._user_cell_left_pad + self._avatar_size + self._user_avatar_gap, 0)
            else:
                column_anchor = "center"
                column_padx = (0, 0)

            label = ctk.CTkLabel(
                header,
                text=text,
                font=("Arial", 12, "bold"),
                text_color=color,
                anchor=column_anchor,
            )
            label.grid(
                row=0,
                column=idx,
                sticky="nsew",
                padx=column_padx,
                pady=(0, 2),
            )
            self._users_header_labels.append(label)

        divider = ctk.CTkFrame(body, fg_color="#EFE6D7", corner_radius=0, height=1)
        divider.grid(row=1, column=0, sticky="ew", padx=(0, self._scrollbar_gutter), pady=(0, 3))

        # Scrollable list of user rows.
        self.rows_scroll = ctk.CTkScrollableFrame(
            body,
            fg_color="#FFFFFF",
            corner_radius=0,
            border_width=0,
            scrollbar_button_color="#D8CAB0",
            scrollbar_button_hover_color="#C9B89A",
            scrollbar_fg_color="#FFFFFF",
        )
        self.rows_scroll.grid(row=2, column=0, sticky="nsew")
        self.rows_scroll.grid_columnconfigure(0, weight=1)

    def _build_permissions_panel(self, parent):
        """Build the role-permissions matrix shown below the users table."""
        panel = ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=20,
            border_width=1,
            border_color="#E3D9C9",
            height=320,
        )
        panel.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)
        self._permissions_panel = panel

        head = ctk.CTkFrame(panel, fg_color="#FFFFFF", corner_radius=0, height=44)
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(8, 0))
        head.grid_columnconfigure(0, weight=1)
        head.grid_propagate(False)
        self._permissions_head = head

        self._permissions_title_label = ctk.CTkLabel(
            head,
            text="Role Permissions Matrix",
            font=("Arial", 20, "bold"),
            text_color="#2C2416",
        )
        self._permissions_title_label.grid(row=0, column=0, sticky="w")

        self._manage_roles_btn = ctk.CTkButton(
            head,
            text="Manage roles",
            command=self._open_manage_roles_modal,
            fg_color="#FFFFFF",
            hover_color="#F4EFE5",
            text_color="#9A7A2E",
            border_width=1,
            border_color="#D8CAB0",
            corner_radius=12,
            width=130,
            height=30,
            font=("Arial", 12, "bold"),
        )
        self._manage_roles_btn.grid(row=0, column=1, sticky="e")

        ctk.CTkFrame(panel, fg_color="#EFE6D7", corner_radius=0, height=1).grid(row=1, column=0, sticky="ew")

        self.permissions_header = ctk.CTkFrame(panel, fg_color="#FFFFFF", corner_radius=0)
        self.permissions_header.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=(16, 16 + self._scrollbar_gutter),
            pady=(4, 0),
        )

        self.permissions_scroll = ctk.CTkScrollableFrame(
            panel,
            fg_color="#FFFFFF",
            corner_radius=0,
            border_width=0,
            scrollbar_button_color="#D8CAB0",
            scrollbar_button_hover_color="#C9B89A",
            scrollbar_fg_color="#FFFFFF",
        )
        self.permissions_scroll.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=(16, 16),
            pady=(6, 12),
        )

        self.permissions_table = ctk.CTkFrame(self.permissions_scroll, fg_color="#FFFFFF", corner_radius=0)
        self.permissions_table.pack(fill="x", expand=True)
        self._apply_permissions_column_layout()
        self._render_permissions_matrix()

    def _on_search_change(self, query):
        """Stores the latest search text and refreshes visible rows."""
        self._last_search_value = (query or "").strip()
        self._search_query = self._last_search_value.casefold()
        self._render_rows()

    def load_users(self):
        """
        Reload user data and permissions from the database, then refresh all
        visible sections that depend on that data.
        """
        self._users = [dict(row) for row in UserDAO.get_all_users()]
        self._permissions_matrix = UserDAO.get_role_permissions()
        AuthController.refresh_current_user()
        self.current_user = AuthController.current_user
        self.role = self._row_value(self.current_user, "role_name", "")
        self.full_name = self._row_value(self.current_user, "full_name", "User")
        self.location = self._row_value(self.current_user, "location", "All Cities")
        self._refresh_summary_cards()
        self._render_rows()
        self._render_permissions_matrix()

    def _render_permissions_matrix(self):
        """Draw the permissions table based on the latest role-permission data."""
        if not hasattr(self, "permissions_table"):
            return

        for child in self.permissions_header.winfo_children():
            child.destroy()
        for child in self.permissions_table.winfo_children():
            child.destroy()
        self._apply_permissions_column_layout()

        labels = ("Permission", "Admin", "Finance", "Front Desk", "Maintenance", "Manager")
        colors = ("#9E8F77", "#1A4A7A", "#3B6D3B", "#6B5D44", "#7A5A0A", "#3C3489")

        for idx, (lbl, color) in enumerate(zip(labels, colors)):
            ctk.CTkLabel(
                self.permissions_header,
                text=lbl,
                font=("Arial", self._permissions_header_font_size, "bold"),
                text_color=color,
                anchor="w" if idx == 0 else "center",
            ).grid(row=0, column=idx, sticky="ew", padx=(14 if idx == 0 else 0, 0), pady=(0, 4))

        for r, (permission_key, permission_label) in enumerate(self.PERMISSION_ROWS, start=1):
            # Divider line before each permission row.
            ctk.CTkFrame(self.permissions_table, fg_color="#EFE6D7", corner_radius=0, height=1).grid(
                row=(r * 2) - 2, column=0, columnspan=6, sticky="ew"
            )

            ctk.CTkLabel(
                self.permissions_table,
                text=permission_label,
                font=("Arial", self._permissions_row_font_size, "bold"),
                text_color="#2C2416",
                anchor="w",
            ).grid(row=(r * 2) - 1, column=0, sticky="ew", padx=14, pady=8)

            # Show tick if permission is enabled for the role; dash otherwise.
            for c, role_key in enumerate(self.ROLE_ORDER, start=1):
                allowed = int(self._permissions_matrix.get(role_key, {}).get(permission_key, 0)) == 1
                ctk.CTkLabel(
                    self.permissions_table,
                    text="✓" if allowed else "—",
                    font=("Arial", self._permissions_mark_font_size, "bold"),
                    text_color="#3B6D3B" if allowed else "#9E8F77",
                    anchor="center",
                ).grid(row=(r * 2) - 1, column=c, sticky="ew", pady=8)

    def _apply_permissions_column_layout(self):
        """Apply matching column widths to the permissions header and body."""
        weights = self._permissions_col_weights
        minsizes = self._compute_permissions_column_minsizes()
        for col, weight in enumerate(weights):
            if minsizes:
                self.permissions_header.grid_columnconfigure(col, weight=weight, minsize=minsizes[col])
                self.permissions_table.grid_columnconfigure(col, weight=weight, minsize=minsizes[col])
            else:
                self.permissions_header.grid_columnconfigure(col, weight=weight)
                self.permissions_table.grid_columnconfigure(col, weight=weight)

    def _compute_permissions_column_minsizes(self):
        """Calculate proportional column sizes based on current widget width."""
        if not hasattr(self, "permissions_header"):
            return None
        total_width = int(self.permissions_header.winfo_width())
        if total_width <= 0:
            return None
        total_weight = sum(self._permissions_col_weights) or 1
        minsizes = [int(total_width * w / total_weight) for w in self._permissions_col_weights]
        remainder = total_width - sum(minsizes)
        if remainder > 0:
            minsizes[-1] += remainder
        return minsizes

    def _refresh_summary_cards(self):
        """Update counts shown in the role summary cards."""
        counts = {k: 0 for k in self._summary_labels}
        for user in self._users:
            key = str(user.get("role_name", "")).strip().lower()
            if key in counts:
                counts[key] += 1
        for key, lbl in self._summary_labels.items():
            lbl.configure(text=str(counts[key]))

    def _show_alerts(self):
        """Display quick user account statistics in an info modal."""
        total_users = len(self._users)
        active_users = sum(1 for u in self._users if int(u.get("is_active", 0)) == 1)
        inactive_users = total_users - active_users

        self.shell.show_premium_info_modal(
            title="User Alerts",
            icon_text="🔔",
            icon_fg="#B8891F",
            icon_bg="#F6E8B8",
            highlight_nonzero=True,
            rows=[
                ("Total users", str(total_users)),
                ("Active users", str(active_users)),
                ("Inactive users", str(inactive_users)),
            ],
        )

    def _show_settings(self):
        """Show account information for the logged-in user."""
        role_text = str(self.role).replace("_", " ").title()
        is_admin = str(self.role).strip().lower() == "admin"
        details_rows = [
            ("User", self.full_name),
            ("Role", role_text),
        ]
        if is_admin:
            details_rows.append(("Location Access", "Full location access (All Cities)"))
        else:
            details_rows.insert(2, ("Location", self.location))
        self.shell.show_premium_info_modal(
            title="Account Settings",
            icon_bg="#F6EED7",
            rows=details_rows,
            icon_image_name="settings",
            icon_image_size=(34, 34),
        )

    def _render_rows(self):
        """Render the user table rows, applying current search filter if needed."""
        for child in self.rows_scroll.winfo_children():
            child.destroy()
        self._row_cards.clear()

        users = self._users
        if self._search_query:
            q = self._search_query
            users = [u for u in users if self._user_matches_query(u, q)]

        for idx, user in enumerate(users):
            user_id = int(user["id"])
            col_minsizes = self._compute_user_column_minsizes()

            row_wrap = ctk.CTkFrame(self.rows_scroll, fg_color="#FFFFFF", corner_radius=0)
            row_wrap.grid(row=idx, column=0, sticky="ew", pady=(0, 0))
            row_wrap.grid_columnconfigure(0, weight=1)

            row = ctk.CTkFrame(
                row_wrap,
                fg_color="#FFFFFF",
                corner_radius=14,
                border_width=1,
                border_color="#FFFFFF",
                height=self._row_height,
            )
            row.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 0))
            row.grid_rowconfigure(0, weight=1)
            for col, weight in enumerate(self._user_col_weights):
                if col_minsizes:
                    row.grid_columnconfigure(col, weight=weight, minsize=col_minsizes[col])
                else:
                    row.grid_columnconfigure(col, weight=weight)
            row.grid_propagate(False)

            divider = ctk.CTkFrame(row_wrap, fg_color="#EFE6D7", corner_radius=0, height=1)
            divider.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 0))

            self._row_cards[user_id] = row

            # Build lightweight avatar from initials if no photo exists.
            initials = "".join(part[0] for part in str(user["full_name"]).split()[:2]).upper() or "U"
            role_key = str(user["role_name"]).strip().lower()
            role_label = self.ROLE_LABELS.get(role_key, str(user["role_name"]).replace("_", " ").title())
            role_bg, role_fg = self.ROLE_COLORS.get(role_key, ("#EDE8DC", "#6B5D44"))
            status_active = int(user.get("is_active", 0)) == 1

            # USER CELL
            user_cell = ctk.CTkFrame(row, fg_color="transparent", corner_radius=0)
            user_cell.grid(
                row=0,
                column=0,
                sticky="nsew",
                padx=(self._user_cell_left_pad, 0),
                pady=8,
            )
            user_cell.grid_rowconfigure(0, weight=1)
            user_cell.grid_columnconfigure(1, weight=1)

            avatar = ctk.CTkLabel(
                user_cell,
                text=initials,
                width=self._avatar_size,
                height=self._avatar_size,
                corner_radius=self._avatar_size // 2,
                fg_color="#F1E6CC",
                text_color="#8A6712",
                font=("Arial", self._avatar_font_size, "bold"),
            )
            avatar.grid(row=0, column=0, padx=(0, 10), pady=0)
            avatar.grid_configure(padx=(0, self._user_avatar_gap))

            name_col = ctk.CTkFrame(user_cell, fg_color="transparent", corner_radius=0)
            name_col.grid(row=0, column=1, sticky="w")

            ctk.CTkLabel(
                name_col,
                text=self._truncate_text(str(user["full_name"]), self._user_name_max_chars),
                text_color="#2C2416",
                font=("Arial", self._name_font_size + 1, "bold"),
                anchor="w",
                fg_color="transparent",
            ).pack(anchor="w")

            # ROLE
            ctk.CTkLabel(
                row,
                text=role_label,
                fg_color=role_bg,
                text_color=role_fg,
                corner_radius=16,
                font=("Arial", self._pill_font_size, "bold"),
                height=self._pill_height + 4,
                width=self._role_pill_width,
            ).grid(row=0, column=1, sticky="n", pady=8)

            # LOCATION
            ctk.CTkLabel(
                row,
                text=user.get("location") or "All Cities",
                text_color="#6B5D44",
                font=("Arial", self._meta_font_size + 1, "bold"),
                fg_color="transparent",
                anchor="center",
            ).grid(row=0, column=2, sticky="n", pady=8)

            # LAST LOGIN
            last_login_text = self._format_last_login(user.get("last_login"))
            ctk.CTkLabel(
                row,
                text=last_login_text,
                text_color="#6B5D44",
                font=("Arial", self._meta_font_size + 1, "bold"),
                fg_color="transparent",
                anchor="center",
            ).grid(row=0, column=3, sticky="n", pady=8)

            # STATUS
            ctk.CTkLabel(
                row,
                text="Active" if status_active else "Inactive",
                text_color="#3B6D3B" if status_active else "#8B2E2E",
                fg_color="#EAF3EA" if status_active else "#F7EBEB",
                corner_radius=16,
                font=("Arial", self._pill_font_size, "bold"),
                width=self._status_width + 12,
                height=self._pill_height + 4,
            ).grid(row=0, column=4, sticky="n", pady=8)

            # Single click selects the row. Double click opens edit modal.
            self._bind_row_select(row, user_id)
            row.bind(
                "<Double-Button-1>",
                lambda _e, uid=user_id: (self._select_row(uid), self._open_selected_for_edit())
            )

        # Keep selection state consistent after re-rendering.
        if self.selected_user_id is not None:
            self._highlight_selected()
        elif users:
            self._select_row(int(users[0]["id"]))
        self._refresh_user_action_buttons()

    def _user_matches_query(self, user, query):
        """
        Search helper.

        Supports:
        - prefix matching for short inputs
        - broader contains matching for longer inputs
        - matching against full name, username, role, location and initials
        """
        def normalize(text):
            return " ".join(str(text or "").replace("_", " ").replace("-", " ").split()).casefold()

        query = normalize(query)
        if not query:
            return True

        raw_role_key = str(user.get("role_name", "")).strip().lower()
        role_key = normalize(raw_role_key)
        role_text = role_key.replace("_", " ")
        role_label = normalize(self.ROLE_LABELS.get(raw_role_key, role_text.title()))
        full_name = normalize(user.get("full_name", ""))
        username = normalize(user.get("username", ""))
        location = normalize(user.get("location", ""))
        initials = "".join(part[0] for part in full_name.split()[:2]).casefold()

        tokens = []
        for field in (full_name, username, role_key, role_text, role_label, location, initials):
            tokens.extend(part for part in field.replace("_", " ").split() if part)

        # One-letter searches behave like quick prefix lookup.
        if len(query) <= 1:
            return any(token.startswith(query) for token in tokens)

        if any(token.startswith(query) for token in tokens):
            return True

        searchable_fields = [full_name, username, role_key, role_text, role_label, location]
        return any(query in field for field in searchable_fields)

    @staticmethod
    def _format_last_login(value):
        """Format ISO datetime into a readable label for the table."""
        text = str(value or "").strip()
        if not text:
            return "Never"
        try:
            dt = datetime.fromisoformat(text)
            return dt.strftime("%d %b %Y, %H:%M")
        except Exception:
            return text

    def _select_row(self, user_id):
        """Store selected row id and refresh selection styling/buttons."""
        self.selected_user_id = user_id
        self._highlight_selected()
        self._refresh_user_action_buttons()

    def _bind_row_select(self, widget, user_id, exclude=None):
        """Recursively bind row selection to the row and its child widgets."""
        exclude = exclude or set()

        if widget not in exclude:
            widget.bind("<Button-1>", lambda _e, uid=user_id: self._select_row(uid))

        for child in widget.winfo_children():
            self._bind_row_select(child, user_id, exclude)

    def _highlight_selected(self):
        """Visually highlight the currently selected user row."""
        for uid, card in self._row_cards.items():
            if uid == self.selected_user_id:
                card.configure(
                    fg_color="#FFFCF6",
                    border_width=2,
                    border_color="#D8CAB0",
                )
            else:
                card.configure(
                    fg_color="#FFFFFF",
                    border_width=1,
                    border_color="#FFFFFF",
                )

    def _open_selected_for_edit(self):
        """Open edit form for the selected user, or first user if none selected."""
        user = None
        if self.selected_user_id is not None:
            user = next((u for u in self._users if int(u["id"]) == self.selected_user_id), None)
        if user is None and self._users:
            user = self._users[0]
            self.selected_user_id = int(user["id"])
            self._highlight_selected()
        if not user:
            messagebox.showerror("Not found", "Could not find selected user.")
            return
        self._open_user_modal(user)

    def _get_selected_user(self):
        """Return the selected user record, or None if nothing is selected."""
        if self.selected_user_id is None:
            return None
        return next((u for u in self._users if int(u["id"]) == self.selected_user_id), None)

    def _refresh_user_action_buttons(self):
        """Enable/disable action buttons based on selected user state."""
        if not hasattr(self, "_update_user_btn") or not hasattr(self, "_toggle_active_btn"):
            return

        user = self._get_selected_user()
        if not user:
            self._update_user_btn.configure(state="disabled")
            self._toggle_active_btn.configure(state="disabled", text="Deactivate", text_color="#9F1D1D")
            return

        self._update_user_btn.configure(state="normal")
        is_active = int(user.get("is_active", 0)) == 1
        if is_active:
            self._toggle_active_btn.configure(state="normal", text="Deactivate", text_color="#9F1D1D")
        else:
            self._toggle_active_btn.configure(state="normal", text="Activate", text_color="#2E6A2E")

    def _toggle_selected_user_active(self):
        """Toggle selected user's active/inactive account state."""
        user = self._get_selected_user()
        if not user:
            messagebox.showerror("Not found", "Please select a user first.")
            return
        is_active = int(user.get("is_active", 0)) == 1
        self._set_user_active_state(user, not is_active)

    def _set_users_header_column_weights(self, weights):
        """Apply column sizing rules to the users table header."""
        self._user_col_weights = tuple(weights)
        col_minsizes = self._compute_user_column_minsizes()
        for col, weight in enumerate(weights):
            if col_minsizes:
                self._users_header.grid_columnconfigure(col, weight=weight, minsize=col_minsizes[col])
            else:
                self._users_header.grid_columnconfigure(col, weight=weight)

    def _compute_user_column_minsizes(self):
        """Calculate responsive column widths for the user table."""
        if not hasattr(self, "_users_body"):
            return None
        total_width = int(self._users_body.winfo_width()) - self._scrollbar_gutter
        if total_width <= 0:
            return None
        total_weight = sum(self._user_col_weights) or 1
        minsizes = [int(total_width * weight / total_weight) for weight in self._user_col_weights]
        remainder = total_width - sum(minsizes)
        if remainder > 0:
            minsizes[-1] += remainder
        return minsizes

    @staticmethod
    def _truncate_text(text, max_chars):
        """Shorten long names so rows remain visually aligned."""
        if max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text
        if max_chars <= 3:
            return text[:max_chars]
        return f"{text[:max_chars - 3]}..."

    def _set_user_active_state(self, user, make_active: bool):
        """Activate or deactivate a user after confirmation."""
        user_id = int(user["id"])
        action_word = "activate" if make_active else "deactivate"
        confirm_word = "Activate" if make_active else "Deactivate"

        confirmed = self._show_confirmation_modal(
            title=f"{confirm_word} User",
            message=f"Are you sure you want to {action_word} '{user['full_name']}'?",
            icon_name="activate" if make_active else "deactivate",
        )
        if not confirmed:
            return

        try:
            if make_active:
                # Use dedicated DAO method if available; otherwise fall back to update.
                if hasattr(UserDAO, "activate_user"):
                    UserDAO.activate_user(user_id)
                else:
                    UserDAO.update_user(
                        user_id,
                        user["full_name"],
                        user["username"],
                        user["role_name"],
                        user.get("location"),
                        1,
                        None,
                    )
            else:
                UserDAO.deactivate_user(user_id)

            self.load_users()
            self._show_status_modal(
                title="Success",
                message=f"User {'activated' if make_active else 'deactivated'} successfully.",
                icon_name="success",
            )
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _show_confirmation_modal(self, title, message, icon_name=None):
        """Reusable confirmation modal returning True or False."""
        return self._show_action_modal(
            title=title,
            message=message,
            icon_name=icon_name,
            confirm_mode=True,
        )

    def _show_status_modal(self, title, message, icon_name=None):
        """Reusable one-button status modal."""
        self._show_action_modal(
            title=title,
            message=message,
            icon_name=icon_name,
            confirm_mode=False,
        )

    def _show_action_modal(self, title, message, icon_name=None, confirm_mode=True):
        """
        Custom modal for confirmations and status messages.

        Uses a Toplevel window with grab_set() to keep user focus on the dialog.
        """
        root = self.winfo_toplevel()
        root.update_idletasks()

        width = 420
        height = 255 if confirm_mode else 235
        x = root.winfo_rootx() + (root.winfo_width() // 2) - (width // 2)
        y = root.winfo_rooty() + (root.winfo_height() // 2) - (height // 2)

        modal = tk.Toplevel(root)
        modal.overrideredirect(True)
        modal.geometry(f"{width}x{height}+{x}+{y}")
        modal.configure(bg="#F8F5F0")
        modal.transient(root)
        modal.grab_set()

        result = {"confirmed": False}

        card = ctk.CTkFrame(
            modal,
            fg_color="#F7F7FA",
            corner_radius=24,
            border_width=1,
            border_color="#E3D9C9",
        )
        card.pack(fill="both", expand=True, padx=6, pady=6)

        body = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)
        ctk.CTkFrame(body, fg_color="transparent", height=18).pack()

        icon_image = self._load_confirmation_icon(icon_name, size=(44, 44))
        if icon_image:
            icon_label = ctk.CTkLabel(body, text="", image=icon_image, fg_color="transparent")
            icon_label._icon_ref = icon_image
            icon_label.pack(pady=(10, 6))
        else:
            ctk.CTkLabel(
                body,
                text="!",
                width=38,
                height=38,
                corner_radius=12,
                fg_color="#F6EED7",
                text_color="#9A7A2E",
                font=("Arial", 18, "bold"),
            ).pack(pady=(10, 6))

        ctk.CTkLabel(
            body,
            text=title,
            text_color="#2C2416",
            font=("Arial", 14, "bold"),
        ).pack()

        ctk.CTkLabel(
            body,
            text=message,
            text_color="#3F4348",
            font=("Arial", 11, "bold"),
            wraplength=360,
            justify="center",
        ).pack(pady=(6, 10))

        actions = ctk.CTkFrame(body, fg_color="transparent", corner_radius=0)
        actions.pack(pady=(0, 10))
        ctk.CTkFrame(body, fg_color="transparent", height=8).pack()

        def close_modal():
            modal.destroy()

        def confirm():
            result["confirmed"] = True
            close_modal()

        if confirm_mode:
            ctk.CTkButton(
                actions,
                text="No",
                command=close_modal,
                fg_color="#D8DBDE",
                hover_color="#C9CDD1",
                text_color="#3F4348",
                corner_radius=16,
                width=135,
                height=38,
                font=("Arial", 12, "normal"),
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                actions,
                text="Yes",
                command=confirm,
                fg_color="#E656A0",
                hover_color="#D84B94",
                text_color="#FFFFFF",
                corner_radius=16,
                width=135,
                height=38,
                font=("Arial", 12, "bold"),
            ).pack(side="left")
        else:
            ctk.CTkButton(
                actions,
                text="OK",
                command=close_modal,
                fg_color="#E656A0",
                hover_color="#D84B94",
                text_color="#FFFFFF",
                corner_radius=16,
                width=140,
                height=38,
                font=("Arial", 12, "bold"),
            ).pack()

        modal.bind("<Escape>", lambda _e: close_modal())
        modal.wait_window()
        return result["confirmed"]

    def _load_confirmation_icon(self, icon_name, size=(72, 72)):
        """Load icon used in custom modal dialogs."""
        if not icon_name or not PIL_AVAILABLE:
            return None
        icon_path = os.path.join("images", "icons", f"{icon_name}.png")
        if not os.path.exists(icon_path) and icon_name == "success":
            icon_path = os.path.join("images", "icons", "activate.png")
        if not os.path.exists(icon_path):
            return None
        try:
            image = Image.open(icon_path).convert("RGBA")
            return ctk.CTkImage(light_image=image, dark_image=image, size=size)
        except Exception:
            return None

    def _delete_user(self, user):
        """Permanently delete a user if DAO support exists."""
        user_id = int(user["id"])

        confirmed = messagebox.askyesno(
            "Delete User",
            f"Are you sure you want to permanently delete '{user['full_name']}'?"
        )
        if not confirmed:
            return

        try:
            if hasattr(UserDAO, "delete_user"):
                UserDAO.delete_user(user_id)
            else:
                messagebox.showwarning(
                    "Not available",
                    "UserDAO.delete_user() is not implemented yet."
                )
                return

            self.selected_user_id = None
            self.load_users()
            messagebox.showinfo("Success", "User deleted.")
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _on_resized(self, _event):
        """Debounce resize events so layout recalculates efficiently."""
        if self._responsive_job:
            try:
                self.after_cancel(self._responsive_job)
            except Exception:
                pass
        self._responsive_job = self.after(120, self._apply_responsive_layout)

    def _apply_responsive_layout(self):
        """
        Adjust fonts, widths, heights and spacing based on current window size.

        This keeps the interface usable on smaller and larger screens.
        """
        self._responsive_job = None
        width = max(self.winfo_width(), self.winfo_toplevel().winfo_width())
        height = max(self.winfo_height(), self.winfo_toplevel().winfo_height())
        if width <= 1 or height <= 1:
            return

        if width < 1300:
            width_mode = "small"
        elif width < 1600:
            width_mode = "medium"
        else:
            width_mode = "large"

        height_mode = "short" if height < 860 else "normal"
        key = (width_mode, height_mode)
        if key == self._responsive_key:
            return
        self._responsive_key = key

        # Small-screen layout values.
        if width_mode == "small":
            role_cols = 5
            role_card_height = 88
            title_font = 10
            note_font = 9
            count_font = 18
            users_panel_height = 350 if height_mode == "short" else 380
            top_height = 52
            users_title_size = 16
            header_height = 22
            header_font = 10
            user_header_weights = (3, 3, 2, 2, 2)
            btn_height = 30
            btn_font = 11
            btn_widths = (132, 120, 136)
            self._row_height = 50
            self._avatar_size = 22
            self._avatar_font_size = 9
            self._user_cell_left_pad = 6
            self._user_avatar_gap = 6
            self._name_font_size = 11
            self._meta_font_size = 10
            self._pill_font_size = 10
            self._pill_height = 22
            self._role_pill_width = 138
            self._status_width = 82
            self._user_name_max_chars = 21
            permissions_panel_height = 220
            permissions_head_height = 38
            permissions_title_font = 17
            permissions_btn_height = 28
            permissions_btn_font = 11
            self._permissions_header_font_size = 10
            self._permissions_row_font_size = 11
            self._permissions_mark_font_size = 12

        # Medium-screen layout values.
        elif width_mode == "medium":
            role_cols = 5
            role_card_height = 92
            title_font = 11
            note_font = 10
            count_font = 20
            users_panel_height = 380 if height_mode == "short" else 405
            top_height = 50
            users_title_size = 17
            header_height = 24
            header_font = 11
            user_header_weights = (3, 3, 2, 2, 2)
            btn_height = 32
            btn_font = 12
            btn_widths = (145, 130, 146)
            self._row_height = 54
            self._avatar_size = 24
            self._avatar_font_size = 9
            self._user_cell_left_pad = 7
            self._user_avatar_gap = 6
            self._name_font_size = 12
            self._meta_font_size = 11
            self._pill_font_size = 11
            self._pill_height = 24
            self._role_pill_width = 146
            self._status_width = 86
            self._user_name_max_chars = 26
            permissions_panel_height = 230
            permissions_head_height = 42
            permissions_title_font = 19
            permissions_btn_height = 30
            permissions_btn_font = 12
            self._permissions_header_font_size = 11
            self._permissions_row_font_size = 12
            self._permissions_mark_font_size = 13

        # Large-screen layout values.
        else:
            role_cols = 5
            role_card_height = 96
            title_font = 12
            note_font = 10
            count_font = 22
            users_panel_height = 395 if height_mode == "short" else 420
            top_height = 50
            users_title_size = 18
            header_height = 26
            header_font = 11
            user_header_weights = (3, 3, 2, 2, 2)
            btn_height = 34
            btn_font = 12
            btn_widths = (155, 136, 152)
            self._row_height = 58
            self._avatar_size = 26
            self._avatar_font_size = 10
            self._user_cell_left_pad = 8
            self._user_avatar_gap = 6
            self._name_font_size = 12
            self._meta_font_size = 11
            self._pill_font_size = 11
            self._pill_height = 24
            self._role_pill_width = 150
            self._status_width = 88
            self._user_name_max_chars = 30
            permissions_panel_height = 240
            permissions_head_height = 44
            permissions_title_font = 20
            permissions_btn_height = 30
            permissions_btn_font = 12
            self._permissions_header_font_size = 11
            self._permissions_row_font_size = 13
            self._permissions_mark_font_size = 14

        # Reapply responsive values to existing widgets.
        for idx, label in enumerate(self._users_header_labels):
            label.configure(font=("Arial", header_font, "bold"))
            if idx == 0:
                label.grid_configure(
                    padx=(self._user_cell_left_pad + self._avatar_size + self._user_avatar_gap, 0)
                )
            else:
                label.grid_configure(padx=(0, 0))

        for idx, item in enumerate(self._role_cards):
            row = idx // role_cols
            col = idx % role_cols
            item["card"].grid(row=row, column=col, sticky="nsew", padx=6, pady=(0, 6))
            item["card"].configure(height=role_card_height)
            item["title"].configure(font=("Arial", title_font, "bold"))
            item["note"].configure(font=("Arial", note_font))
            item["count"].configure(font=("Georgia", count_font, "bold"))

        for col in range(5):
            self._role_cards_wrap.grid_columnconfigure(col, weight=0)
        for col in range(role_cols):
            self._role_cards_wrap.grid_columnconfigure(col, weight=1)

        self._users_panel.configure(height=users_panel_height)
        self._users_top.configure(height=top_height)
        self._users_title_label.configure(font=("Arial", users_title_size, "bold"))
        self._users_header.configure(height=header_height)
        self._set_users_header_column_weights(user_header_weights)

        self._add_user_btn.configure(
            height=btn_height,
            width=btn_widths[0],
            font=("Arial", btn_font, "bold")
        )
        self._update_user_btn.configure(
            height=btn_height,
            width=btn_widths[1],
            font=("Arial", btn_font, "bold")
        )
        self._toggle_active_btn.configure(
            height=btn_height,
            width=btn_widths[2],
            font=("Arial", btn_font, "bold")
        )

        self._users_actions.grid(row=0, column=1, sticky="e", pady=0)
        self._add_user_btn.grid(row=0, column=0, padx=0, pady=0, sticky="e")
        self._update_user_btn.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="e")
        self._toggle_active_btn.grid(row=0, column=2, padx=(10, 0), pady=0, sticky="e")

        self._permissions_panel.configure(height=permissions_panel_height)
        self._permissions_head.configure(height=permissions_head_height)
        self._permissions_title_label.configure(font=("Arial", permissions_title_font, "bold"))
        self._manage_roles_btn.configure(height=permissions_btn_height, font=("Arial", permissions_btn_font, "bold"))

        # Re-render components whose layout depends on these values.
        self._render_permissions_matrix()
        self._render_rows()

    def _open_user_modal(self, user=None):
        """Open modal used for both adding and editing users."""
        is_edit = user is not None
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit User" if is_edit else "Add User")
        self._center_dialog(dialog, 560, 520)
        dialog.grab_set()
        dialog.configure(fg_color="#F8F5F0")
        dialog.after(30, lambda: (dialog.lift(), dialog.focus_force()))

        body = ctk.CTkFrame(dialog, fg_color="#F8F5F0", corner_radius=0)
        body.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            body,
            text="Edit User Access" if is_edit else "Add New User",
            text_color="#2C2416",
            font=("Georgia", 32, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 14))

        form = ctk.CTkFrame(
            body,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color="#E3D9C9",
        )
        form.pack(fill="both", expand=True)
        form.grid_columnconfigure(1, weight=1)

        def add_row(label, idx):
            ctk.CTkLabel(form, text=label, text_color="#6B5D44", font=("Arial", 14, "bold")).grid(
                row=idx, column=0, sticky="w", padx=18, pady=10
            )

        add_row("Full Name", 0)
        full_name = ctk.CTkEntry(form, height=40, corner_radius=12)
        full_name.grid(row=0, column=1, sticky="ew", padx=12, pady=10)

        add_row("Username", 1)
        username = ctk.CTkEntry(form, height=40, corner_radius=12)
        username.grid(row=1, column=1, sticky="ew", padx=12, pady=10)

        add_row("Password", 2)
        password = ctk.CTkEntry(form, height=40, corner_radius=12, show="*")
        password.grid(row=2, column=1, sticky="ew", padx=12, pady=10)
        if is_edit:
            # Password may be left blank during edit to keep existing password.
            password.configure(placeholder_text="Leave blank to keep current password")

        add_row("Role", 3)
        roles = UserDAO.get_roles()
        role_combo = ctk.CTkComboBox(form, values=roles, state="readonly", height=40, corner_radius=12)
        role_combo.grid(row=3, column=1, sticky="ew", padx=12, pady=10)
        if roles:
            role_combo.set(roles[0])

        add_row("Location", 4)
        location_combo = ctk.CTkComboBox(
            form,
            values=self.LOCATION_VALUES,
            state="readonly",
            height=40,
            corner_radius=12,
        )
        location_combo.grid(row=4, column=1, sticky="ew", padx=12, pady=10)
        location_combo.set(self.LOCATION_VALUES[0])

        active_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            form,
            text="Active account",
            variable=active_var,
            text_color="#564A36",
            font=("Arial", 13, "bold"),
        ).grid(row=5, column=1, sticky="w", padx=12, pady=(0, 10))

        # Pre-fill fields when editing an existing user.
        if is_edit:
            full_name.insert(0, user["full_name"])
            username.insert(0, user["username"])
            role_combo.set(str(user["role_name"]))
            loc = user.get("location")
            if loc in self.LOCATION_VALUES:
                location_combo.set(loc)
            active_var.set(int(user.get("is_active", 0)) == 1)

        actions = ctk.CTkFrame(body, fg_color="#F8F5F0", corner_radius=0)
        actions.pack(fill="x", pady=(12, 0))

        ctk.CTkButton(
            actions,
            text="Cancel",
            command=dialog.destroy,
            fg_color="#EEE7D9",
            hover_color="#E2D8C6",
            text_color="#5E5137",
            corner_radius=12,
            width=110,
            height=40,
            font=("Arial", 14, "bold"),
        ).pack(side="right", padx=(10, 0))

        def submit():
            """Validate fields, then create or update the user in the DAO."""
            full = full_name.get().strip()
            usern = username.get().strip()
            pwd = password.get().strip()
            role = role_combo.get().strip()
            location = location_combo.get().strip() or None
            is_active = 1 if active_var.get() else 0

            if not full or not usern or not role:
                messagebox.showerror("Error", "Full name, username and role are required.")
                return
            if not is_edit and not pwd:
                messagebox.showerror("Error", "Password is required for new users.")
                return
            if pwd and len(pwd) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters.")
                return

            try:
                if is_edit:
                    UserDAO.update_user(
                        int(user["id"]),
                        full,
                        usern,
                        role,
                        location,
                        is_active,
                        pwd or None,
                    )
                else:
                    UserDAO.create_user(full, usern, pwd, role, location, is_active)

                dialog.destroy()
                self.load_users()
                messagebox.showinfo("Success", "User saved successfully.")
            except Exception as err:
                messagebox.showerror("Error", str(err))

        ctk.CTkButton(
            actions,
            text="Save User",
            command=submit,
            fg_color="#1C170F",
            hover_color="#2B2417",
            text_color="#C9A84C",
            border_width=1,
            border_color="#6B5624",
            corner_radius=12,
            width=130,
            height=40,
            font=("Arial", 14, "bold"),
        ).pack(side="right")

    def _open_manage_roles_modal(self):
        """Open modal that allows editing role-permission mappings."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Manage Role Permissions")
        self._center_dialog(dialog, 860, 460)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color="#F8F5F0")

        body = ctk.CTkFrame(dialog, fg_color="#F8F5F0", corner_radius=0)
        body.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            body,
            text="Manage Role Permissions",
            text_color="#2C2416",
            font=("Georgia", 30, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        matrix_wrap = ctk.CTkFrame(
            body,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color="#E3D9C9",
        )
        matrix_wrap.pack(fill="both", expand=True)
        for idx, weight in enumerate(self._permissions_col_weights):
            matrix_wrap.grid_columnconfigure(idx, weight=weight)

        role_headers = ("Permission", "Admin", "Finance", "Front Desk", "Maintenance", "Manager")
        for idx, header in enumerate(role_headers):
            ctk.CTkLabel(
                matrix_wrap,
                text=header,
                text_color="#9E8F77" if idx == 0 else "#2C2416",
                font=("Arial", 13, "bold"),
                anchor="w" if idx == 0 else "center",
            ).grid(row=0, column=idx, sticky="ew", padx=(16 if idx == 0 else 0, 0), pady=(16, 12))

        vars_map = {}
        for row_idx, (permission_key, permission_label) in enumerate(self.PERMISSION_ROWS, start=1):
            ctk.CTkFrame(matrix_wrap, fg_color="#EFE6D7", corner_radius=0, height=1).grid(
                row=(row_idx * 2) - 1, column=0, columnspan=6, sticky="ew"
            )
            ctk.CTkLabel(
                matrix_wrap,
                text=permission_label,
                text_color="#2C2416",
                font=("Arial", 14, "bold"),
                anchor="w",
            ).grid(row=row_idx * 2, column=0, sticky="ew", padx=16, pady=10)

            vars_map[permission_key] = {}
            for col_idx, role_key in enumerate(self.ROLE_ORDER, start=1):
                value = int(self._permissions_matrix.get(role_key, {}).get(permission_key, 0)) == 1
                var = tk.BooleanVar(value=value)
                vars_map[permission_key][role_key] = var

                ctk.CTkCheckBox(
                    matrix_wrap,
                    text="",
                    variable=var,
                    width=24,
                    checkbox_width=20,
                    checkbox_height=20,
                    corner_radius=6,
                ).grid(row=row_idx * 2, column=col_idx)

        actions = ctk.CTkFrame(body, fg_color="#F8F5F0", corner_radius=0)
        actions.pack(fill="x", pady=(12, 0))

        ctk.CTkButton(
            actions,
            text="Cancel",
            command=dialog.destroy,
            fg_color="#EEE7D9",
            hover_color="#E2D8C6",
            text_color="#5E5137",
            corner_radius=12,
            width=110,
            height=40,
            font=("Arial", 14, "bold"),
        ).pack(side="right", padx=(10, 0))

        def save_permissions():
            """Collect checkbox values and save the updated permission matrix."""
            updated = {role: {} for role in self.ROLE_ORDER}
            for permission_key, _permission_label in self.PERMISSION_ROWS:
                for role_key in self.ROLE_ORDER:
                    updated[role_key][permission_key] = 1 if vars_map[permission_key][role_key].get() else 0
            try:
                UserDAO.update_role_permissions(updated)
                self._permissions_matrix = UserDAO.get_role_permissions()
                self._render_permissions_matrix()
                dialog.destroy()
                messagebox.showinfo("Success", "Role permissions updated.")
            except Exception as err:
                messagebox.showerror("Error", str(err))

        ctk.CTkButton(
            actions,
            text="Save Permissions",
            command=save_permissions,
            fg_color="#1C170F",
            hover_color="#2B2417",
            text_color="#C9A84C",
            border_width=1,
            border_color="#6B5624",
            corner_radius=12,
            width=165,
            height=40,
            font=("Arial", 14, "bold"),
        ).pack(side="right")

    def _center_dialog(self, dialog, width, height):
        """Position modal dialog in the centre of the main application window."""
        dialog.update_idletasks()
        root = self.winfo_toplevel()
        root.update_idletasks()
        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        rw, rh = root.winfo_width(), root.winfo_height()
        x = rx + max(0, (rw - width) // 2)
        y = ry + max(0, (rh - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
