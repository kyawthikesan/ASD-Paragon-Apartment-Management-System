# Student Name: Nang Phwe Hleng Hun
# Student ID: 24043841
# Module: UFCF8S-30-2 Advanced Software Development

# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

import tkinter as tk
import os
from datetime import date

import customtkinter as ctk

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    # PIL is optional here. If it is not installed, the view will still work,
    # but popup images will fall back to basic handling.
    Image = None
    PIL_AVAILABLE = False

from controllers.apartment_controller import ApartmentController
from controllers.auth_controller import AuthController
from dao.lease_dao import LeaseDAO
from dao.location_dao import LocationDAO
from dao.maintenance_dao import MaintenanceDAO
from views.premium_shell import PremiumAppShell


class ApartmentView(tk.Frame):
    PAGE_BG = "#F8F5F0"
    CARD_BG = "#FFFFFF"
    BORDER = "#E2D7C5"
    BORDER_SOFT = "#E9DDCA"
    LABEL = "#89775D"
    TEXT = "#2B2419"
    MUTED = "#7E705A"
    ACCENT = "#C3A04B"
    ACCENT_HOVER = "#AF8F45"
    POPUP_PINK = "#D95B9A"
    POPUP_PINK_HOVER = "#C94F8D"
    CARD_HEIGHT = 108
    CARD_ROW_HEIGHT = 88

    STATUS_COLORS = {
        "Occupied": {"bg": "#DCEBDD", "fg": "#2F6B3F"},
        "Vacant": {"bg": "#F3EBDD", "fg": "#7A5A0A"},
        "Maintenance Hold": {"bg": "#F3DEDE", "fg": "#8B3030"},
    }

    @staticmethod
    def _read(record, key, default=None):
        # Small helper so the view can safely read either dicts or row-like objects
        # without repeating the same error handling everywhere.
        if record is None:
            return default
        if isinstance(record, dict):
            value = record.get(key, default)
            return default if value is None else value
        try:
            value = record[key]
            return default if value is None else value
        except Exception:
            return default

    def _popup_parent(self):
        return self.winfo_toplevel()

    def _center_window(self, window, parent=None):
        # Center popups relative to the main app window so dialogs do not appear
        # in odd positions on the screen.
        host = parent or self._popup_parent()
        window.update_idletasks()
        host.update_idletasks()

        width = window.winfo_width()
        height = window.winfo_height()
        if width <= 1 or height <= 1:
            # Some new windows report size too early, so fall back to geometry text.
            geom = window.geometry().split("+")[0]
            if "x" in geom:
                try:
                    width, height = [int(v) for v in geom.split("x", 1)]
                except Exception:
                    width, height = 420, 320

        host_x = host.winfo_rootx()
        host_y = host.winfo_rooty()
        host_w = host.winfo_width()
        host_h = host.winfo_height()

        x = host_x + max((host_w - width) // 2, 0)
        y = host_y + max((host_h - height) // 2, 0)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def __init__(
        self,
        parent,
        back_callback,
        open_lease_management=None,
        open_user_management=None,
        open_tenant_management=None,
        open_maintenance_dashboard=None,
        open_finance_payments=None,
        open_finance_reports=None,
    ):
        super().__init__(parent, bg=self.PAGE_BG)
        self.pack(fill="both", expand=True)

        # Cache current user's access details once when the page loads.
        self.is_admin = AuthController.is_admin()
        self.city_scope = AuthController.get_city_scope()
        self.role = AuthController.get_current_role()
        self.can_modify_apartments = AuthController.can_perform_action("edit_apartments", self.role)
        self.can_create_leases = AuthController.can_perform_action("create_leases", self.role)
        self.open_lease_management = open_lease_management
        self.open_user_management = open_user_management or back_callback
        self.open_tenant_management = open_tenant_management or back_callback
        self.open_maintenance_dashboard = open_maintenance_dashboard or back_callback
        self.open_finance_payments = open_finance_payments or back_callback
        self.open_finance_reports = open_finance_reports or back_callback

        # State used for search/filtering and quick lookups.
        self.search_text = ""
        self.active_filter = "All Units"
        self.all_apartments = []
        self.lease_by_apartment = {}
        self.maintenance_hold_ids = set()
        self.location_map = {}
        self._property_popup_icon = None
        self._property_popup_image = None
        self._property_popup_ctk_image = None

        nav_sections = [
            {"title": "Overview", "items": [{"label": "Dashboard", "action": back_callback, "icon": "dashboard"}]},
            {
                "title": "Management",
                "items": [
                    {"label": "Tenants", "action": self.open_tenant_management, "icon": "tenants"},
                    {"label": "Apartments", "action": lambda: None, "icon": "apartments"},
                ],
            },
            {"title": "Finance", "items": []},
            {"title": "Admin", "items": []},
        ]

        # Build sidebar items based on the logged-in user's permissions.
        if AuthController.can_access_feature("lease_management", self.role):
            nav_sections[1]["items"].append(
                {
                    "label": "Leases",
                    "action": self.open_lease_management or back_callback,
                    "icon": "leases",
                }
            )
        if AuthController.can_access_feature("maintenance_management", self.role):
            nav_sections[1]["items"].append(
                {"label": "Maintenance", "action": self.open_maintenance_dashboard, "icon": "maintenance"}
            )
        if AuthController.can_access_feature("finance_dashboard", self.role):
            nav_sections[2]["items"].append(
                {
                    "label": "Payments & Reports",
                    "action": self.open_finance_payments,
                    "icon": "payments",
                }
            )
        # Keep User Access visible for consistent sidebar layout across roles.
        nav_sections[3]["items"].append(
            {"label": "User Access", "action": self.open_user_management, "icon": "shield"}
        )

        self.shell = PremiumAppShell(
            self,
            page_title="Apartment Management",
            on_logout=back_callback,
            active_nav="Apartments",
            nav_sections=nav_sections,
            footer_action_label="Back to Dashboard",
            search_placeholder="Search apartments...",
            on_search_change=self._on_search_change,
            on_search_submit=self._on_search_change,
            on_bell_click=self._show_alerts,
            on_settings_click=self._show_settings,
            notification_count=self._estimate_alert_count(),
        )
        self.content = self.shell.content

        self.load_locations()
        self._build_ui()
        self.load_apartments()

    def _build_ui(self):
        # Top summary cards.
        self.stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.stats_row.pack(fill="x", pady=(4, 12))
        self.stats_row.grid_columnconfigure(0, weight=1)
        self.stats_row.grid_columnconfigure(1, weight=1)
        self.stats_row.grid_columnconfigure(2, weight=1)
        self.stats_row.grid_columnconfigure(3, weight=1)

        self.stat_values = {}
        self._make_stat_card(0, "TOTAL UNITS", "0")
        self._make_stat_card(1, "OCCUPIED", "0", value_color="#2F6B3F")
        self._make_stat_card(2, "VACANT", "0", value_color="#7A5A0A")
        self._make_stat_card(3, "MAINTENANCE HOLD", "0", value_color="#8B3030")

        # Filter buttons and add-apartment action.
        filter_row = ctk.CTkFrame(self.content, fg_color="transparent")
        filter_row.pack(fill="x", pady=(0, 12))

        self.filter_buttons = {}
        for label in ["All Units", "Occupied", "Vacant", "Maintenance Hold"]:
            btn = ctk.CTkButton(
                filter_row,
                text=label,
                height=34,
                corner_radius=19,
                font=("Segoe UI", 12, "bold"),
                command=lambda value=label: self._set_filter(value),
            )
            btn.pack(side="left", padx=(0, 10))
            self.filter_buttons[label] = btn
        self._refresh_filter_styles()

        if self.can_modify_apartments:
            ctk.CTkButton(
                filter_row,
                text="+ Add Apartment",
                height=38,
                width=188,
                corner_radius=16,
                fg_color="#F3EEE5",
                hover_color="#ECE2D2",
                text_color=self.TEXT,
                border_width=1,
                border_color="#CDBEA6",
                font=("Segoe UI", 13, "bold"),
                command=self._open_add_dialog,
            ).pack(side="right")

        # Main list container for apartment cards.
        self.list_wrap = ctk.CTkFrame(
            self.content,
            fg_color=self.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER,
        )
        self.list_wrap.pack(fill="both", expand=True)

        self.cards_area = ctk.CTkScrollableFrame(
            self.list_wrap,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#D7C8AE",
            scrollbar_button_hover_color="#C8B28F",
        )
        self.cards_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.cards_area.grid_columnconfigure(0, weight=1)

    def _make_stat_card(self, column, label, value, value_color=None):
        card = ctk.CTkFrame(
            self.stats_row,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
            height=108,
        )
        card.grid(row=0, column=column, padx=(0 if column == 0 else 8, 0), sticky="ew")
        card.grid_propagate(False)

        ctk.CTkLabel(
            card,
            text=label,
            text_color="#9A8A70",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 4))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            text_color=value_color or self.TEXT,
            font=("Georgia", 28, "bold"),
            anchor="w",
        )
        value_label.pack(fill="x", padx=16, pady=(0, 10))
        self.stat_values[label] = value_label

    def _set_filter(self, value):
        self.active_filter = value
        self._refresh_filter_styles()
        self._render_apartment_cards()

    def _refresh_filter_styles(self):
        # Highlight the selected filter so the current view is obvious.
        for label, button in self.filter_buttons.items():
            active = label == self.active_filter
            button.configure(
                fg_color=self.ACCENT if active else "#FFFFFF",
                hover_color=self.ACCENT_HOVER if active else "#F4ECDC",
                text_color="#FFFFFF" if active else "#6B5D44",
                border_width=1,
                border_color=self.ACCENT if active else "#D7C8AE",
            )

    def _on_search_change(self, query):
        self.search_text = (query or "").strip()
        self._render_apartment_cards()

    def load_locations(self):
        # Non-admin users only see locations inside their assigned city scope.
        locations = LocationDAO.get_all_locations()
        if not self.is_admin and self.city_scope:
            locations = [loc for loc in locations if str(loc["city"]).strip() == self.city_scope]
        self.location_map = {loc["city"]: loc["location_id"] for loc in locations}

    def load_apartments(self):
        # Refresh everything the page depends on, then redraw the UI.
        self.all_apartments = [dict(row) for row in ApartmentController.get_all_apartments(city=self.city_scope)]
        self.lease_by_apartment = self._build_active_lease_map()
        self.maintenance_hold_ids = self._build_maintenance_hold_set()
        self._update_stats()
        self._render_apartment_cards()

    def _build_active_lease_map(self):
        # Keep only the most relevant active lease for each apartment.
        lease_map = {}
        leases = LeaseDAO.get_all_leases_with_financial_details(city=self.city_scope)
        for lease in leases:
            if str(lease.get("status", "")).strip().lower() != "active":
                continue
            apartment_id = lease.get("apartmentID")
            if apartment_id not in lease_map:
                lease_map[apartment_id] = lease
                continue

            # If duplicates exist, keep the one with the latest end date.
            previous_end = str(lease_map[apartment_id].get("end_date") or "")
            current_end = str(lease.get("end_date") or "")
            if current_end > previous_end:
                lease_map[apartment_id] = lease
        return lease_map

    def _build_maintenance_hold_set(self):
        # Any apartment with an open/pending maintenance request is treated as on hold.
        hold_ids = set()
        active_states = {"open", "in progress", "pending", "new"}
        for item in MaintenanceDAO.get_all_requests(city=self.city_scope):
            apartment_id = item.get("apartmentID")
            if not apartment_id:
                continue
            status = str(item.get("status") or "").strip().lower()
            if status in active_states:
                hold_ids.add(apartment_id)
        return hold_ids

    def _estimate_alert_count(self):
        # Notification badge combines vacancies and maintenance issues.
        apartments = ApartmentController.get_all_apartments(city=self.city_scope)
        holds = self._build_maintenance_hold_set()
        vacant_count = 0
        for apt in apartments:
            status = str(self._read(apt, "status", "")).upper()
            if status != "OCCUPIED":
                vacant_count += 1
        return len(holds) + vacant_count

    def _normalize_status(self, apartment):
        # The UI uses a business-friendly status, not just the raw DB value.
        apartment_id = apartment["apartmentID"]
        if apartment_id in self.maintenance_hold_ids:
            return "Maintenance Hold"

        raw = str(self._read(apartment, "status", "")).strip().upper()
        if raw == "OCCUPIED":
            return "Occupied"
        return "Vacant"

    def _update_stats(self):
        counts = {"TOTAL UNITS": 0, "OCCUPIED": 0, "VACANT": 0, "MAINTENANCE HOLD": 0}

        for apartment in self.all_apartments:
            counts["TOTAL UNITS"] += 1
            normalized = self._normalize_status(apartment)
            if normalized == "Occupied":
                counts["OCCUPIED"] += 1
            elif normalized == "Vacant":
                counts["VACANT"] += 1
            elif normalized == "Maintenance Hold":
                counts["MAINTENANCE HOLD"] += 1

        for key, label in self.stat_values.items():
            label.configure(text=str(counts[key]))

    def _filtered_apartments(self):
        keyword = self.search_text.lower()
        rows = []
        for apartment in self.all_apartments:
            normalized_status = self._normalize_status(apartment)
            if self.active_filter != "All Units" and normalized_status != self.active_filter:
                continue

            # Search checks a combined string so one search box can match
            # apartment details, tenant info, and lease end date.
            lease = self.lease_by_apartment.get(apartment["apartmentID"], {})
            search_blob = " ".join(
                [
                    str(self._read(apartment, "apartmentID", "")),
                    str(self._read(apartment, "city", "")),
                    str(self._read(apartment, "type", "")),
                    str(self._read(apartment, "rooms", "")),
                    str(self._read(apartment, "status", "")),
                    str(lease.get("tenant_name", "")),
                    str(lease.get("end_date", "")),
                ]
            ).lower()

            if keyword and keyword not in search_blob:
                continue
            rows.append(apartment)
        return rows

    def _render_apartment_cards(self):
        # Clear and rebuild the list each time the filter/search changes.
        for child in self.cards_area.winfo_children():
            child.destroy()

        apartments = self._filtered_apartments()
        if not apartments:
            ctk.CTkLabel(
                self.cards_area,
                text="No apartments match your current filter.",
                text_color=self.MUTED,
                font=("Segoe UI", 14),
            ).pack(fill="x", padx=10, pady=14)
            return

        for apartment in apartments:
            self._render_card(apartment)

    def _render_card(self, apartment):
        card = ctk.CTkFrame(
            self.cards_area,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_SOFT,
            height=self.CARD_HEIGHT,
        )
        card.pack(fill="x", padx=6, pady=(0, 8))
        card.pack_propagate(False)

        row = ctk.CTkFrame(card, fg_color="transparent", height=self.CARD_ROW_HEIGHT)
        row.pack(fill="x", padx=14, pady=8)
        row.pack_propagate(False)
        row.grid_columnconfigure(1, weight=1)

        # Left badge shows a short apartment code for easier scanning.
        left_code = ctk.CTkFrame(
            row,
            fg_color="#F1EBDF",
            corner_radius=16,
            border_width=1,
            border_color="#D8C5A1",
            width=70,
            height=70,
        )
        left_code.grid(row=0, column=0, padx=(0, 14), sticky="w")
        left_code.pack_propagate(False)

        ctk.CTkLabel(
            left_code,
            text=self._unit_code(apartment["apartmentID"]),
            text_color="#9A7A2E",
            font=("Georgia", 15, "bold"),
        ).pack(expand=True)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, padx=(0, 12), sticky="w")

        ctk.CTkLabel(
            info,
            text=self._unit_title(apartment),
            text_color=self.TEXT,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            justify="left",
        ).pack(fill="x")

        ctk.CTkLabel(
            info,
            text=self._unit_meta(apartment),
            text_color="#8F8169",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(
            info,
            text=self._tenant_line(apartment),
            text_color="#6F604A",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(2, 0))

        status = self._normalize_status(apartment)
        palette = self.STATUS_COLORS[status]

        right_block = ctk.CTkFrame(row, fg_color="transparent")
        right_block.grid(row=0, column=2, sticky="e")

        status_box = ctk.CTkFrame(right_block, fg_color="transparent", width=112, height=32)
        status_box.pack(side="left", padx=(0, 14))
        status_box.pack_propagate(False)

        ctk.CTkLabel(
            status_box,
            text=status,
            text_color=palette["fg"],
            fg_color=palette["bg"],
            corner_radius=14,
            font=("Segoe UI", 9, "bold"),
            anchor="center",
            justify="center",
        ).pack(fill="both", expand=True)

        rent_box = ctk.CTkFrame(right_block, fg_color="transparent", width=110, height=44)
        rent_box.pack(side="left", padx=(0, 12))
        rent_box.pack_propagate(False)

        ctk.CTkLabel(
            rent_box,
            text=self._format_rent(self._read(apartment, "rent", 0)),
            text_color="#9A7A2E",
            font=("Georgia", 16, "bold"),
            anchor="e",
        ).pack(fill="x")
        ctk.CTkLabel(
            rent_box,
            text="/month",
            text_color="#8F8169",
            font=("Segoe UI", 10, "bold"),
            anchor="e",
        ).pack(fill="x")

        actions = ctk.CTkFrame(right_block, fg_color="transparent")
        actions.pack(side="left")

        ctk.CTkButton(
            actions,
            text="View",
            width=72,
            height=32,
            corner_radius=16,
            fg_color="#F6F3ED",
            hover_color="#ECE4D7",
            text_color=self.TEXT,
            border_width=1,
            border_color="#CFC1AB",
            font=("Segoe UI", 10, "bold"),
            command=lambda unit=apartment: self._show_unit_details(unit),
        ).pack(side="left", padx=(0, 6))
        if status == "Vacant" and self.can_create_leases:
            # Vacant units get a quick shortcut to assignment.
            ctk.CTkButton(
                actions,
                text="Assign",
                width=84,
                height=32,
                corner_radius=16,
                fg_color=self.ACCENT,
                hover_color=self.ACCENT_HOVER,
                text_color="#FFFFFF",
                border_width=1,
                border_color=self.ACCENT,
                font=("Segoe UI", 10, "bold"),
                command=lambda unit=apartment: self._assign_apartment(unit),
            ).pack(side="left")
        elif self.can_modify_apartments:
            ctk.CTkButton(
                actions,
                text="Edit",
                width=72,
                height=32,
                corner_radius=16,
                fg_color="#F6F3ED",
                hover_color="#ECE4D7",
                text_color=self.TEXT,
                border_width=1,
                border_color="#CFC1AB",
                font=("Segoe UI", 10, "bold"),
                command=lambda unit=apartment: self._open_edit_dialog(unit),
            ).pack(side="left")

    def _unit_code(self, apartment_id):
        # Format IDs into a cleaner label for display.
        try:
            return f"A-{int(apartment_id):03d}"
        except (TypeError, ValueError):
            return str(apartment_id)

    def _unit_title(self, apartment):
        apartment_type = str(self._read(apartment, "type", "Apartment")).strip()
        if "apartment" in apartment_type.lower():
            return apartment_type
        return f"{apartment_type} Apartment"

    def _unit_meta(self, apartment):
        city = self._read(apartment, "city", "Unknown city")
        rooms = self._read(apartment, "rooms", "-")
        return f"{city} · {rooms} room(s)"

    def _tenant_line(self, apartment):
        lease = self.lease_by_apartment.get(apartment["apartmentID"])
        if not lease:
            return "No active tenant assignment"
        tenant = lease.get("tenant_name") or "Unknown tenant"
        end_date = lease.get("end_date") or "-"
        return f"Tenant: {tenant} · Lease ends {end_date}"

    def _format_rent(self, value):
        # Show whole numbers without decimals, but keep pence if needed.
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return "£0"
        if numeric.is_integer():
            return f"£{int(numeric):,}"
        return f"£{numeric:,.2f}"

    def _show_unit_details(self, apartment):
        lease = self.lease_by_apartment.get(apartment["apartmentID"])
        details = [
            f"Unit: {self._unit_code(apartment['apartmentID'])}",
            f"Type: {self._read(apartment, 'type', '')}",
            f"City: {self._read(apartment, 'city', '')}",
            f"Rooms: {self._read(apartment, 'rooms', '')}",
            f"Status: {self._normalize_status(apartment)}",
            f"Rent: {self._format_rent(self._read(apartment, 'rent', 0))} /month",
        ]
        if lease:
            details.append(f"Tenant: {lease.get('tenant_name')}")
            details.append(f"Lease End: {lease.get('end_date')}")
        self._show_property_popup("Apartment Details", details)

    def _show_property_popup(
        self,
        title,
        lines,
        show_icon=True,
        text_size=11,
        popup_width=390,
        icon_name="property",
        icon_size=72,
        compact=False,
        center_content=False,
    ):
        # Reusable popup used across the page for details, success messages, and errors.
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.configure(fg_color="#FFFFFF")
        line_count = max(len(lines), 1)
        if compact:
            popup_height = max(210, min(280, 96 + (line_count * 22) + (58 if show_icon else 0)))
        else:
            popup_height = max(220, min(360, 150 + (line_count * 26) + (88 if show_icon else 0)))
        popup.geometry(f"{popup_width}x{popup_height}")
        popup.resizable(False, False)
        popup.transient(self._popup_parent())
        popup.grab_set()
        self._center_window(popup, self._popup_parent())

        icon_path = os.path.join("images", "icons", f"{icon_name}.png")
        if show_icon and os.path.exists(icon_path):
            try:
                full_icon = tk.PhotoImage(file=icon_path)
                self._property_popup_icon = full_icon
                popup.iconphoto(True, self._property_popup_icon)

                # The window icon can stay full size, but the visible image inside the popup
                # needs to be reduced so it does not dominate the modal.
                max_size = icon_size
                width = max(full_icon.width(), 1)
                height = max(full_icon.height(), 1)
                ratio = max(width / max_size, height / max_size, 1)
                scale = int(ratio)
                self._property_popup_image = full_icon.subsample(scale, scale)

                # Use CTkImage when PIL is available to avoid HighDPI scaling warnings.
                if PIL_AVAILABLE:
                    pil_image = Image.open(icon_path).convert("RGBA")
                    self._property_popup_ctk_image = ctk.CTkImage(
                        light_image=pil_image,
                        size=(icon_size, icon_size),
                    )
                else:
                    self._property_popup_ctk_image = None
            except Exception:
                # If image loading fails, still show the popup without the icon.
                self._property_popup_icon = None
                self._property_popup_image = None
                self._property_popup_ctk_image = None

        wrap = ctk.CTkFrame(
            popup,
            fg_color="#FFFFFF",
            corner_radius=14,
            border_width=1,
            border_color="#E2D7C5",
        )
        wrap.pack(fill="both", expand=True, padx=14, pady=14)
        content_parent = wrap
        if center_content:
            content_parent = ctk.CTkFrame(wrap, fg_color="transparent")
            content_parent.pack(expand=True, pady=(8, 6))

        if show_icon and self._property_popup_ctk_image is not None:
            ctk.CTkLabel(content_parent, text="", image=self._property_popup_ctk_image).pack(pady=(8, 10))
        elif show_icon and self._property_popup_image is not None:
            tk.Label(content_parent, text="", image=self._property_popup_image, bg="#FFFFFF").pack(pady=(8, 10))

        details_text = "\n".join(lines)
        ctk.CTkLabel(
            content_parent,
            text=details_text,
            text_color="#3A3226",
            font=("Segoe UI", text_size, "bold"),
            justify="center",
            wraplength=popup_width - 60,
        ).pack(padx=12, pady=(4, 10))

        ctk.CTkButton(
            content_parent,
            text="OK",
            height=34,
            width=110,
            corner_radius=12,
            fg_color=self.POPUP_PINK,
            hover_color=self.POPUP_PINK_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            command=popup.destroy,
        ).pack(pady=(0, 8))

    def _show_error_popup(self, message):
        self._show_property_popup("Error", [message])

    def _show_confirm_popup(self, title, message):
        # Custom confirm dialog so the UI style stays consistent with the rest of the app.
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.configure(fg_color="#FFFFFF")
        popup.geometry("420x260")
        popup.resizable(False, False)
        popup.transient(self._popup_parent())
        popup.grab_set()
        self._center_window(popup, self._popup_parent())

        choice = {"confirmed": False}
        wrap = ctk.CTkFrame(
            popup,
            fg_color="#FFFFFF",
            corner_radius=14,
            border_width=1,
            border_color="#E2D7C5",
        )
        wrap.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(
            wrap,
            text=message,
            text_color="#3A3226",
            font=("Segoe UI", 15, "bold"),
            justify="center",
            wraplength=340,
        ).pack(padx=16, pady=(36, 22))

        actions = ctk.CTkFrame(wrap, fg_color="transparent")
        actions.pack(pady=(0, 14))

        def close_with(value):
            choice["confirmed"] = value
            popup.destroy()

        ctk.CTkButton(
            actions,
            text="No",
            height=36,
            width=110,
            corner_radius=12,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#C9BCA7",
            font=("Segoe UI", 13, "bold"),
            command=lambda: close_with(False),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            actions,
            text="Yes",
            height=36,
            width=110,
            corner_radius=12,
            fg_color=self.POPUP_PINK,
            hover_color=self.POPUP_PINK_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 13, "bold"),
            command=lambda: close_with(True),
        ).pack(side="left")

        popup.wait_window()
        return choice["confirmed"]

    def _assign_apartment(self, apartment):
        if not self.can_create_leases:
            self._show_error_popup("Your role can view apartment occupancy but cannot assign leases.")
            return
        # If lease management is available, send the user there directly.
        if callable(self.open_lease_management):
            self.open_lease_management()
            return
        self._show_property_popup(
            "Assign Tenant",
            [f"Use Lease Management to assign a tenant to {self._unit_code(apartment['apartmentID'])}."],
        )

    def _show_alerts(self):
        maintenance_holds = len(self.maintenance_hold_ids)
        vacant_count = sum(1 for apt in self.all_apartments if self._normalize_status(apt) == "Vacant")
        expiring_soon = 0
        for lease in self.lease_by_apartment.values():
            end_date = str(lease.get("end_date") or "")
            if not end_date:
                continue
            try:
                days_left = (date.fromisoformat(end_date) - date.today()).days
                if 0 <= days_left <= 30:
                    expiring_soon += 1
            except Exception:
                continue

        self.shell.show_premium_info_modal(
            title="Alerts",
            rows=[
                ("Vacant units to assign", str(vacant_count)),
                ("Maintenance holds", str(maintenance_holds)),
                ("Leases ending in 30 days", str(expiring_soon)),
            ],
            highlight_nonzero=True,
            icon_bg="#F6EED7",
            icon_image_name="property",
            icon_image_size=(34, 34),
        )

    def _show_settings(self):
        user = AuthController.current_user or {}
        name = self._read(user, "full_name", "Unknown")
        role = str(self._read(user, "role_name", "-")).replace("_", " ").title()
        location = self._read(user, "location", "All cities")
        is_admin = str(role).strip().lower() == "admin"

        rows = [
            ("User", name),
            ("Role", role),
        ]
        if is_admin:
            rows.append(("Location Access", "Full location access (All Cities)"))
        else:
            rows.append(("Location", location))

        self.shell.show_premium_info_modal(
            title="Account Settings",
            rows=rows,
            icon_bg="#F6EED7",
            icon_image_name="settings",
            icon_image_size=(34, 34),
        )

    def _open_add_dialog(self):
        if not self.can_modify_apartments:
            self._show_error_popup("Your role has read-only access to apartment records.")
            return
        self._open_apartment_dialog(mode="add")

    def _open_edit_dialog(self, apartment):
        if not self.can_modify_apartments:
            self._show_error_popup("Your role has read-only access to apartment records.")
            return
        self._open_apartment_dialog(mode="edit", apartment=apartment)

    def _open_apartment_dialog(self, mode, apartment=None):
        if not self.can_modify_apartments:
            self._show_error_popup("Your role has read-only access to apartment records.")
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Apartment" if mode == "add" else "Edit Apartment")
        dialog.configure(fg_color=self.PAGE_BG)
        dialog.geometry("560x620")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        self._center_window(dialog, self._popup_parent())

        form = ctk.CTkFrame(
            dialog,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
        )
        form.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            form,
            text="Add Apartment" if mode == "add" else f"Edit {self._unit_code(apartment['apartmentID'])}",
            text_color=self.TEXT,
            font=("Georgia", 24, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 6))

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=12, pady=6)
        fields.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(fields, text="Location", text_color=self.LABEL, font=("Segoe UI", 12, "bold"), anchor="w").grid(
            row=0, column=0, sticky="w", pady=(2, 0)
        )
        location_combo = ctk.CTkComboBox(
            fields,
            values=list(self.location_map.keys()) or [""],
            width=500,
            height=38,
            corner_radius=10,
            border_color="#CEC3B2",
            button_color="#D8C6A3",
            button_hover_color="#C9B38A",
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#EFE5D5",
            fg_color="#FCFAF6",
            text_color="#2B2419",
        )
        location_combo.grid(row=1, column=0, sticky="ew", pady=(2, 8))

        ctk.CTkLabel(fields, text="Type", text_color=self.LABEL, font=("Segoe UI", 12, "bold"), anchor="w").grid(
            row=2, column=0, sticky="w", pady=(2, 0)
        )
        type_entry = ctk.CTkEntry(
            fields,
            height=38,
            corner_radius=10,
            border_color="#CEC3B2",
            fg_color="#FCFAF6",
            text_color="#2B2419",
            placeholder_text="e.g. 2-Bedroom Apartment",
        )
        type_entry.grid(row=3, column=0, sticky="ew", pady=(2, 8))

        ctk.CTkLabel(fields, text="Rent", text_color=self.LABEL, font=("Segoe UI", 12, "bold"), anchor="w").grid(
            row=4, column=0, sticky="w", pady=(2, 0)
        )
        rent_entry = ctk.CTkEntry(
            fields,
            height=38,
            corner_radius=10,
            border_color="#CEC3B2",
            fg_color="#FCFAF6",
            text_color="#2B2419",
            placeholder_text="e.g. 1200",
        )
        rent_entry.grid(row=5, column=0, sticky="ew", pady=(2, 8))

        ctk.CTkLabel(fields, text="Rooms", text_color=self.LABEL, font=("Segoe UI", 12, "bold"), anchor="w").grid(
            row=6, column=0, sticky="w", pady=(2, 0)
        )
        rooms_entry = ctk.CTkEntry(
            fields,
            height=38,
            corner_radius=10,
            border_color="#CEC3B2",
            fg_color="#FCFAF6",
            text_color="#2B2419",
            placeholder_text="e.g. 2",
        )
        rooms_entry.grid(row=7, column=0, sticky="ew", pady=(2, 8))

        if self.location_map:
            first_city = next(iter(self.location_map))
            location_combo.set(first_city)

        if mode == "edit" and apartment:
            # Pre-fill form fields so the user can edit existing values directly.
            location_combo.set(str(self._read(apartment, "city", "")))
            type_entry.insert(0, str(self._read(apartment, "type", "")))
            rent_entry.insert(0, str(self._read(apartment, "rent", "")))
            rooms_entry.insert(0, str(self._read(apartment, "rooms", "")))

        if not self.is_admin:
            # Restrict non-admin users to their assigned location.
            location_combo.configure(state="disabled")

        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.pack(fill="x", padx=12, pady=(2, 12))

        def submit():
            # Validate user input before calling the controller.
            selected_city = location_combo.get().strip()
            if not selected_city:
                self._show_error_popup("Location is required.")
                return
            if not AuthController.can_access_city(selected_city):
                self._show_error_popup("You can only manage apartments in your assigned location.")
                return
            if selected_city not in self.location_map:
                self._show_error_popup("Selected location is invalid.")
                return

            apt_type = type_entry.get().strip()
            rent = rent_entry.get().strip()
            rooms = rooms_entry.get().strip()

            if not apt_type or not rent or not rooms:
                self._show_error_popup("All fields are required.")
                return

            try:
                rent_value = float(rent)
            except ValueError:
                self._show_error_popup("Rent must be a valid number.")
                return

            try:
                rooms_value = int(rooms)
            except ValueError:
                self._show_error_popup("Rooms must be a whole number.")
                return

            if rooms_value <= 0 or rent_value < 0:
                self._show_error_popup("Rent and rooms must be positive values.")
                return

            location_id = self.location_map[selected_city]

            try:
                if mode == "add":
                    ApartmentController.add_apartment(location_id, apt_type, rent_value, rooms_value)
                    self._show_property_popup("Success", ["Apartment added successfully."])
                else:
                    ApartmentController.update_apartment(
                        apartment["apartmentID"],
                        location_id,
                        apt_type,
                        rent_value,
                        rooms_value,
                    )
                    self._show_property_popup("Updated", ["Apartment updated successfully."])
            except Exception as error:
                self._show_error_popup(f"Unable to save apartment. {error}")
                return

            dialog.destroy()
            self.load_apartments()

        ctk.CTkButton(
            actions,
            text="Save",
            height=36,
            width=120,
            corner_radius=12,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            text_color="#1F1A12",
            font=("Segoe UI", 13, "bold"),
            command=submit,
        ).pack(side="right")

        ctk.CTkButton(
            actions,
            text="Cancel",
            height=36,
            width=120,
            corner_radius=12,
            fg_color="#F6F1E8",
            hover_color="#EDE3D4",
            text_color=self.TEXT,
            border_width=1,
            border_color="#C9BCA7",
            font=("Segoe UI", 13, "bold"),
            command=dialog.destroy,
        ).pack(side="right", padx=(0, 8))

        if mode == "edit" and apartment:
            def delete_current():
                confirmed = self._show_confirm_popup(
                    "Delete Apartment",
                    f"Delete {self._unit_code(apartment['apartmentID'])}? This cannot be undone.",
                )
                if not confirmed:
                    return
                try:
                    ApartmentController.delete_apartment(apartment["apartmentID"])
                except Exception as error:
                    error_text = str(error)
                    if "FOREIGN KEY" in error_text.upper():
                        self._show_error_popup(
                            "Cannot delete this apartment because it has related records (lease/payment/history)."
                        )
                    else:
                        self._show_error_popup(f"Unable to delete apartment. {error_text}")
                    return
                dialog.destroy()
                self.load_apartments()
                self._show_property_popup("Deleted", ["Apartment deleted successfully."])

            ctk.CTkButton(
                actions,
                text="Delete",
                height=36,
                width=120,
                corner_radius=12,
                fg_color="#F3DFDF",
                hover_color="#EBCFCF",
                text_color="#8B3030",
                border_width=1,
                border_color="#DFC0C0",
                font=("Segoe UI", 13, "bold"),
                command=delete_current,
            ).pack(side="left")
