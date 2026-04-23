# Student Name: Nang Phwe Hleng Hun
# Student ID: 24043841
# Module: UFCF8S-30-2 Advanced Software Development


# Student Name: Shune Pyae Pyae (Evelyn) Aung 
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date

import customtkinter as ctk

from controllers.tenant_controller import TenantController
from controllers.auth_controller import AuthController
from views.premium_shell import PremiumAppShell


class TenantView(tk.Frame):
    PAGE_BG = "#F8F5F0"
    CARD_BG = "#FFFFFF"
    BORDER = "#E2D7C5"
    BORDER_SOFT = "#EEE5D7"
    LABEL = "#89775D"
    TEXT = "#2B2419"
    MUTED = "#7E705A"
    ACCENT = "#C3A04B"
    ACCENT_HOVER = "#AF8F45"

    STATUS_STYLES = {
        "Active": {"bg": "#DAEBDD", "fg": "#2F6B3F"},
        "Expiring Soon": {"bg": "#F4E7CB", "fg": "#8A6828"},
        "Notice Given": {"bg": "#F2DCDC", "fg": "#8B3030"},
        "New": {"bg": "#DCE8F7", "fg": "#2A5F96"},
    }

    AVATAR_PALETTE = ["#EFE2CA", "#D7E5F5", "#DAE9DB", "#EEDDDD", "#E4E0F4"]

    def __init__(
        self,
        parent,
        back_callback,
        open_user_management=None,
        open_apartment_management=None,
        open_lease_management=None,
        open_maintenance_dashboard=None,
        open_maintenance_management=None,
        open_finance_payments=None,
        open_finance_reports=None,
    ):
        super().__init__(parent, bg=self.PAGE_BG)
        self.pack(fill="both", expand=True)

        self.city_scope = AuthController.get_city_scope()
        self.role = AuthController.get_current_role()
        self.can_manage_tenants = AuthController.can_perform_action("register_tenants", self.role)
        self.active_filter = "All Tenants"
        self.search_text = ""
        self.selected_tenant_id = None
        self.current_tenants = []
        self.current_edit_tenant = None
        self.open_user_management = open_user_management or back_callback
        self.open_apartment_management = open_apartment_management or back_callback
        self.open_lease_management = open_lease_management or back_callback
        self.open_maintenance_management = (
            open_maintenance_dashboard
            or open_maintenance_management
            or back_callback
        )
        self.open_finance_payments = open_finance_payments or back_callback
        self.open_finance_reports = open_finance_reports or back_callback

        nav_sections = [
            {
                "title": "Overview",
                "items": [{"label": "Dashboard", "action": back_callback, "icon": "dashboard"}],
            },
            {
                "title": "Management",
                "items": [
                    {"label": "Tenants", "action": lambda: None, "icon": "tenants"},
                ],
            },
            {"title": "Finance", "items": []},
            {"title": "Admin", "items": []},
        ]
        if AuthController.can_access_feature("apartment_management", self.role):
            nav_sections[1]["items"].append(
                {
                    "label": "Apartments",
                    "action": self.open_apartment_management,
                    "icon": "apartments",
                }
            )
        if AuthController.can_access_feature("lease_management", self.role):
            nav_sections[1]["items"].append(
                {"label": "Leases", "action": self.open_lease_management, "icon": "leases"}
            )
        if AuthController.can_access_feature("maintenance_management", self.role):
            nav_sections[1]["items"].append(
                {
                    "label": "Maintenance",
                    "action": self.open_maintenance_management,
                    "icon": "maintenance",
                }
            )
        if AuthController.can_access_feature("finance_dashboard", self.role):
            nav_sections[2]["items"].append(
                {
                    "label": "Payments & Reports",
                    "action": self.open_finance_payments,
                    "icon": "payments",
                }
            )
        nav_sections[3]["items"].append(
            {"label": "User Access", "action": self.open_user_management, "icon": "shield"}
        )

        self.shell = PremiumAppShell(
            self,
            page_title="Tenant Management",
            on_logout=back_callback,
            active_nav="Tenants",
            nav_sections=nav_sections,
            footer_action_label="Back to Dashboard",
            search_placeholder="Search tenants...",
            on_search_change=self._on_search_change,
            on_search_submit=self._on_search_change,
            on_bell_click=self._show_alerts,
            on_settings_click=self._show_settings,
        )

        self.content = self.shell.content
        self._build_ui()
        self.load_tenants()

    def _build_ui(self):
        filter_row = ctk.CTkFrame(self.content, fg_color="transparent")
        filter_row.pack(fill="x", pady=(2, 14))

        self.filter_buttons = {}
        filters = ["All Tenants", "Active", "Expiring Soon", "Notice Given"]

        for label in filters:
            btn = ctk.CTkButton(
                filter_row,
                text=label,
                width=128,
                height=38,
                corner_radius=19,
                command=lambda value=label: self._set_filter(value),
                font=("Segoe UI", 13, "bold"),
            )
            btn.pack(side="left", padx=(0, 10))
            self.filter_buttons[label] = btn

        self._refresh_filter_styles()

        if self.can_manage_tenants:
            self.register_btn = ctk.CTkButton(
                filter_row,
                text="+ Register New Tenant",
                height=40,
                width=216,
                corner_radius=20,
                fg_color="#F2ECE0",
                text_color=self.TEXT,
                border_width=1,
                border_color="#D0C1A8",
                hover_color="#EADFCF",
                font=("Segoe UI", 15, "bold"),
                command=self._open_register_form,
            )
            self.register_btn.pack(side="right")
        else:
            self.register_btn = None

        self.cards_wrap = ctk.CTkFrame(
            self.content,
            fg_color=self.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER,
        )
        self.cards_wrap.pack(fill="both", expand=True, pady=(0, 12))

        self.cards_area = ctk.CTkScrollableFrame(
            self.cards_wrap,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#D7C8AE",
            scrollbar_button_hover_color="#C8B28F",
        )
        self.cards_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.cards_area.grid_columnconfigure(0, weight=1)
        self.cards_area.grid_columnconfigure(1, weight=1)
        self.cards_area.grid_columnconfigure(2, weight=1)
        self._bind_scroll_recursive(self.cards_area)
        self._enable_global_cards_scroll()

        self.form_card = ctk.CTkFrame(
            self.content,
            fg_color="#F6F1E8",
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER,
        )
        self._build_form_card()
        self.form_visible = False

    def _build_form_card(self):
        header = ctk.CTkFrame(self.form_card, fg_color="transparent", height=34)
        header.pack(fill="x", padx=14, pady=(8, 0))
        header.pack_propagate(False)

        self.form_title = ctk.CTkLabel(
            header,
            text="Register New Tenant",
            text_color=self.TEXT,
            font=("Georgia", 18, "bold"),
            anchor="w",
        )
        self.form_title.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            header,
            text="✕",
            width=24,
            height=24,
            corner_radius=10,
            fg_color="transparent",
            hover_color="#EDE3D4",
            text_color="#8F826D",
            font=("Segoe UI", 12, "bold"),
            command=self._close_form,
        ).pack(side="right")

        ctk.CTkLabel(
            self.form_card,
            text="Tip: click any tenant card to edit quickly.",
            text_color=self.MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 4))

        fields = ctk.CTkFrame(self.form_card, fg_color="transparent")
        fields.pack(fill="x", padx=12)
        fields.grid_columnconfigure(0, weight=1)
        fields.grid_columnconfigure(1, weight=1)
        fields.grid_columnconfigure(2, weight=1)

        self.name = self._make_entry(fields, "FULL NAME", "e.g. John Smith", 0, 0)
        self.NI_number = self._make_entry(fields, "NI NUMBER", "AB123456C", 0, 1)
        self.phone = self._make_entry(fields, "PHONE NUMBER", "07700000000", 0, 2)
        self.NI_number.bind("<KeyRelease>", self.uppercase_ni)
        self.phone.bind("<KeyRelease>", lambda _event, widget=self.phone: self._enforce_digits_only(widget))

        self.email = self._make_entry(fields, "EMAIL ADDRESS", "john@gmail.com", 1, 0)
        self.occupation = self._make_entry(fields, "OCCUPATION", "e.g. Teacher", 1, 1)
        self.reference = self._make_entry(fields, "REFERENCES", "Employer / previous landlord", 1, 2)

        ctk.CTkFrame(self.form_card, fg_color="#D9CDB8", height=1).pack(fill="x", pady=(6, 6))

        actions = ctk.CTkFrame(self.form_card, fg_color="transparent", height=36)
        actions.pack(fill="x", padx=12, pady=(0, 8))
        actions.pack_propagate(False)

        self.delete_btn = ctk.CTkButton(
            actions,
            text="Delete Tenant",
            width=102,
            height=30,
            corner_radius=10,
            fg_color="#F4E7E7",
            hover_color="#EED7D7",
            text_color="#8E2F2F",
            border_width=1,
            border_color="#DFC0C0",
            font=("Segoe UI", 10, "bold"),
            command=self.delete_tenant,
        )

        ctk.CTkButton(
            actions,
            text="Cancel",
            width=86,
            height=30,
            corner_radius=10,
            fg_color="#FAF7F2",
            hover_color="#ECE4D7",
            text_color=self.TEXT,
            border_width=1,
            border_color="#C9BCA7",
            font=("Segoe UI", 10, "bold"),
            command=self.clear_fields,
        ).pack(side="right", padx=(0, 8))

        self.primary_btn = ctk.CTkButton(
            actions,
            text="Register Tenant",
            width=146,
            height=30,
            corner_radius=10,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            text_color="#221E17",
            border_width=1,
            border_color="#A9893C",
            font=("Segoe UI", 10, "bold"),
            command=self.add_tenant,
        )
        self.primary_btn.pack(side="right")

    def _make_entry(self, parent, label, placeholder, row, col, columnspan=1):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=col, columnspan=columnspan, sticky="ew", padx=4, pady=2)

        ctk.CTkLabel(
            wrap,
            text=label,
            text_color=self.LABEL,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 2))

        entry = ctk.CTkEntry(
            wrap,
            height=34,
            corner_radius=10,
            border_width=1,
            border_color="#CEC3B2",
            fg_color="#FCFAF6",
            text_color="#222222",
            placeholder_text=placeholder,
            placeholder_text_color="#9B9081",
            font=("Segoe UI", 11),
        )
        entry.pack(fill="x")
        return entry

    def _set_filter(self, label):
        self.active_filter = label
        self._refresh_filter_styles()
        self._render_cards()

    def _refresh_filter_styles(self):
        for label, btn in self.filter_buttons.items():
            if label == self.active_filter:
                btn.configure(
                    fg_color=self.ACCENT,
                    hover_color=self.ACCENT,
                    text_color="#FFFFFF",
                    border_width=0,
                )
            else:
                btn.configure(
                    fg_color="#F9F5EE",
                    hover_color="#EEE4D5",
                    text_color="#68593E",
                    border_width=1,
                    border_color="#D8C8AB",
                )

    def _open_register_form(self, reset=True):
        if not self.can_manage_tenants:
            messagebox.showwarning("Read-only Access", "Your role can view tenant records but cannot modify them.")
            return
        if reset:
            self.clear_fields()
        if not self.form_visible:
            self.form_card.pack(fill="x", pady=(0, 0))
            self.form_visible = True
        self.form_card.lift()

    def _close_form(self):
        self.clear_fields()
        self.form_card.pack_forget()
        self.form_visible = False

    def _on_search_change(self, value):
        self.search_text = (value or "").strip().lower()
        self._render_cards()

    def load_tenants(self):
        self.current_tenants = TenantController.get_all_tenants(city=self.city_scope)
        self._render_cards()

    def _show_alerts(self):
        total = len(self.current_tenants)
        active_count = 0
        expiring_count = 0
        notice_count = 0
        unassigned_count = 0

        for tenant in self.current_tenants:
            status = self._display_status(tenant)
            if status == "Active":
                active_count += 1
            elif status == "Expiring Soon":
                expiring_count += 1
            elif status == "Notice Given":
                notice_count += 1

            if not tenant.get("apartmentID"):
                unassigned_count += 1

        self.shell.show_premium_info_modal(
            title="Tenant Alerts",
            icon_text="🔔",
            icon_fg="#B8891F",
            icon_bg="#F6E8B8",
            highlight_nonzero=True,
            rows=[
                ("Total tenants", str(total)),
                ("Active leases", str(active_count)),
                ("Expiring soon", str(expiring_count)),
                ("Notice given", str(notice_count)),
                ("No unit assigned", str(unassigned_count)),
            ],
        )

    def _show_settings(self):
        user = getattr(AuthController, "current_user", None)
        full_name = self._row_value(user, "full_name", "Unknown User")
        location = self._row_value(user, "location", self.city_scope or "All Cities") or (self.city_scope or "All Cities")

        role_text = str(self.role).replace("_", " ").title()
        is_admin = str(self.role).strip().lower() == "admin"
        rows = [
            ("User", full_name),
            ("Role", role_text),
        ]
        if is_admin:
            rows.append(("Location Access", "Full location access (All Cities)"))
        else:
            rows.insert(2, ("Location", location))

        self.shell.show_premium_info_modal(
            title="Account Settings",
            icon_bg="#F6EED7",
            rows=rows,
            icon_image_name="settings",
            icon_image_size=(34, 34),
        )

    @staticmethod
    def _row_value(row, key, fallback=""):
        if row is None:
            return fallback
        try:
            return row[key]
        except Exception:
            return fallback

    def _render_cards(self):
        for child in self.cards_area.winfo_children():
            child.destroy()

        filtered = self._filtered_tenants(self.current_tenants)

        if not filtered:
            empty = ctk.CTkFrame(
                self.cards_area,
                fg_color="#FBF8F3",
                border_width=1,
                border_color=self.BORDER,
                corner_radius=16,
                height=120,
            )
            empty.grid(row=0, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            empty.grid_propagate(False)
            ctk.CTkLabel(
                empty,
                text="No tenants match this filter.",
                text_color=self.MUTED,
                font=("Segoe UI", 15, "bold"),
            ).place(relx=0.5, rely=0.5, anchor="center")
            return

        for index, tenant in enumerate(filtered):
            row = index // 3
            col = index % 3
            card = self._build_tenant_card(self.cards_area, tenant, index)
            card.grid(row=row, column=col, sticky="n", padx=8, pady=6)
            self._bind_scroll_recursive(card)

    def _filtered_tenants(self, tenants):
        output = []
        for tenant in tenants:
            status = self._display_status(tenant)
            haystack = " ".join(
                [
                    str(tenant.get("name", "")),
                    str(tenant.get("NI_number", "")),
                    str(tenant.get("phone", "")),
                    str(tenant.get("email", "")),
                    str(tenant.get("city", "")),
                    str(tenant.get("apartment_type", "")),
                ]
            ).lower()

            if self.search_text and self.search_text not in haystack:
                continue

            if self.active_filter == "All Tenants":
                output.append(tenant)
            elif self.active_filter == status:
                output.append(tenant)

        return output

    def _build_tenant_card(self, parent, tenant, index):
        status = self._display_status(tenant)
        status_label = "Expiring" if status == "Expiring Soon" else status
        style = self.STATUS_STYLES.get(status, self.STATUS_STYLES["New"])

        card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD_BG,
            border_width=1,
            border_color=self.BORDER,
            corner_radius=16,
            width=320,
            height=190,
        )
        card.pack_propagate(False)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=9, pady=(7, 3))

        initials = "".join(part[0] for part in str(tenant.get("name", "")).split()[:2]).upper() or "TN"
        avatar_bg = self.AVATAR_PALETTE[index % len(self.AVATAR_PALETTE)]

        ctk.CTkLabel(
            top,
            text=initials,
            width=30,
            height=30,
            corner_radius=15,
            fg_color=avatar_bg,
            text_color="#6B4E19",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 6))

        title_col = ctk.CTkFrame(top, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col,
            text=tenant.get("name") or "Unknown Tenant",
            text_color=self.TEXT,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill="x")

        unit_text = self._unit_text(tenant)
        ctk.CTkLabel(
            title_col,
            text=unit_text,
            text_color=self.MUTED,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            top,
            text=status_label,
            fg_color=style["bg"],
            text_color=style["fg"],
            corner_radius=11,
            width=68,
            height=20,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="right")

        ctk.CTkFrame(card, fg_color="#EDE2D2", height=1).pack(fill="x", padx=9, pady=(0, 2))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=9, pady=(0, 3))

        fields = [
            ("NI Number", tenant.get("NI_number") or "-"),
            ("Occupation", "Not provided"),
            ("Lease Period", self._format_period(tenant.get("start_date"), tenant.get("end_date"))),
            ("Monthly Rent", self._format_rent(tenant.get("rent"))),
            ("Phone", tenant.get("phone") or "-"),
            ("Reference", self._reference_text(tenant)),
        ]

        for label, value in fields:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=(0, 1))
            ctk.CTkLabel(
                row,
                text=label,
                text_color=self.LABEL,
                font=("Segoe UI", 8, "bold"),
                anchor="w",
                width=70,
            ).pack(side="left", anchor="w")
            ctk.CTkLabel(
                row,
                text=value,
                text_color=self.TEXT,
                font=("Segoe UI", 8, "bold"),
                anchor="e",
            ).pack(side="right", anchor="e")
            ctk.CTkFrame(body, fg_color=self.BORDER_SOFT, height=1).pack(fill="x", pady=(1, 0))

        self._bind_click_recursive(card, lambda _e, t=tenant: self._select_tenant(t))
        return card

    def _bind_click_recursive(self, widget, callback):
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click_recursive(child, callback)

    def _bind_scroll_recursive(self, widget):
        widget.bind("<MouseWheel>", self._on_cards_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_cards_mousewheel_up, add="+")
        widget.bind("<Button-5>", self._on_cards_mousewheel_down, add="+")
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child)

    def _enable_global_cards_scroll(self):
        # Make wheel scrolling reliable even when nested widgets steal focus.
        self.bind_all("<MouseWheel>", self._on_global_cards_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_global_cards_mousewheel_up, add="+")
        self.bind_all("<Button-5>", self._on_global_cards_mousewheel_down, add="+")
        self.bind("<Destroy>", self._on_view_destroy, add="+")

    def _on_view_destroy(self, event=None):
        # Remove global bindings when this view is destroyed.
        if event is not None and event.widget is not self:
            return
        try:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        except Exception:
            pass

    def _pointer_inside_cards(self):
        if not hasattr(self, "cards_wrap") or not self.cards_wrap.winfo_exists():
            return False
        px, py = self.winfo_pointerx(), self.winfo_pointery()
        x = self.cards_wrap.winfo_rootx()
        y = self.cards_wrap.winfo_rooty()
        w = self.cards_wrap.winfo_width()
        h = self.cards_wrap.winfo_height()
        return x <= px <= (x + w) and y <= py <= (y + h)

    def _scroll_cards(self, units):
        canvas = getattr(self.cards_area, "_parent_canvas", None)
        if canvas is not None:
            canvas.yview_scroll(units, "units")

    def _on_cards_mousewheel(self, event):
        # Windows/macOS mouse wheel
        if getattr(event, "delta", 0) == 0:
            return
        step = -1 if event.delta > 0 else 1
        self._scroll_cards(step)

    def _on_cards_mousewheel_up(self, _event):
        # Linux wheel up
        self._scroll_cards(-1)

    def _on_cards_mousewheel_down(self, _event):
        # Linux wheel down
        self._scroll_cards(1)

    def _on_global_cards_mousewheel(self, event):
        if self._pointer_inside_cards():
            self._on_cards_mousewheel(event)

    def _on_global_cards_mousewheel_up(self, event):
        if self._pointer_inside_cards():
            self._on_cards_mousewheel_up(event)

    def _on_global_cards_mousewheel_down(self, event):
        if self._pointer_inside_cards():
            self._on_cards_mousewheel_down(event)

    def _select_tenant(self, tenant):
        if not self.can_manage_tenants:
            return
        self.current_edit_tenant = tenant
        self.selected_tenant_id = tenant.get("tenantID")

        self._open_register_form(reset=False)
        self.form_title.configure(text=f"Edit Tenant #{self.selected_tenant_id}")
        self.primary_btn.configure(text="Update Tenant")

        if not self.delete_btn.winfo_manager():
            self.delete_btn.pack(side="left")

        self._set_entry_value(self.name, tenant.get("name", ""))
        self._set_entry_value(self.NI_number, tenant.get("NI_number", ""))
        self._set_entry_value(self.phone, tenant.get("phone", ""))
        self._set_entry_value(self.email, tenant.get("email", ""))
        self._set_entry_value(self.occupation, "")
        self._set_entry_value(self.reference, tenant.get("email") or "")

    def _set_entry_value(self, entry, value):
        entry.delete(0, tk.END)
        if value:
            entry.insert(0, str(value))

    def validate_phone(self, value):
        return value.isdigit() or value == ""

    def uppercase_ni(self, event):
        current = self.NI_number.get()
        self.NI_number.delete(0, tk.END)
        self.NI_number.insert(0, current.upper())
        self.NI_number.icursor(tk.END)

    def _enforce_digits_only(self, entry):
        current = entry.get()
        cleaned = "".join(ch for ch in current if ch.isdigit())
        if current != cleaned:
            entry.delete(0, tk.END)
            entry.insert(0, cleaned)
            entry.icursor(tk.END)

    def _show_success_modal(self, title, message):
        self.shell.show_premium_info_modal(
            title=title,
            rows=[("Status", message)],
            icon_bg="#FCE1EF",
            icon_image_name="success",
            icon_image_size=(32, 32),
            button_text="OK",
        )

    def _show_required_modal(self, message):
        root = self.winfo_toplevel()
        root.update_idletasks()

        width = 460
        height = 280
        x = root.winfo_rootx() + (root.winfo_width() // 2) - (width // 2)
        y = root.winfo_rooty() + (root.winfo_height() // 2) - (height // 2)

        modal = tk.Toplevel(root)
        modal.overrideredirect(True)
        modal.configure(bg=self.PAGE_BG)
        modal.geometry(f"{width}x{height}+{x}+{y}")

        card = ctk.CTkFrame(
            modal,
            fg_color="#F7F7FA",
            corner_radius=22,
            border_width=1,
            border_color="#E3D9C9",
        )
        card.pack(fill="both", expand=True, padx=8, pady=8)

        icon_circle = ctk.CTkFrame(
            card,
            width=82,
            height=82,
            corner_radius=41,
            fg_color="#FCE1EF",
        )
        icon_circle.pack(pady=(18, 12))
        icon_circle.pack_propagate(False)

        icon_image = self.shell._load_local_modal_icon("require", size=(40, 40))
        if icon_image:
            label = tk.Label(icon_circle, image=icon_image, bg="#FCE1EF", bd=0, highlightthickness=0)
            label.image = icon_image
            label.pack(expand=True)
        else:
            tk.Label(
                icon_circle,
                text="!",
                bg="#FCE1EF",
                fg="#C84D8E",
                font=("Arial", 28, "bold"),
                bd=0,
                highlightthickness=0,
            ).pack(expand=True)

        ctk.CTkLabel(
            card,
            text=message,
            text_color=self.TEXT,
            font=("Segoe UI", 14, "bold"),
            justify="center",
            wraplength=380,
        ).pack(pady=(0, 18))

        def close_modal():
            try:
                modal.grab_release()
            except Exception:
                pass
            modal.destroy()

        ctk.CTkButton(
            card,
            text="OK",
            command=close_modal,
            fg_color="#E656A0",
            hover_color="#D84B94",
            text_color="#FFFFFF",
            corner_radius=16,
            font=("Arial", 16, "bold"),
            height=42,
            width=190,
        ).pack(pady=(0, 18))

        modal.bind("<Escape>", lambda _e: close_modal())
        modal.lift()
        modal.focus_force()
        modal.grab_set()

    def add_tenant(self):
        if not self.can_manage_tenants:
            messagebox.showwarning("Read-only Access", "Your role can view tenant records but cannot modify them.")
            return
        name = self.name.get().strip()
        ni_number = self.NI_number.get().strip().upper()
        phone = self.phone.get().strip()
        email = self.email.get().strip()

        if not name or not ni_number:
            self._show_required_modal("Name and NI Number are required")
            return

        if not phone:
            self._show_required_modal("Phone number is required")
            return

        if not self.validate_phone(phone):
            messagebox.showerror("Error", "Phone number can only contain numbers")
            return

        if self.selected_tenant_id:
            TenantController.update_tenant(self.selected_tenant_id, name, ni_number, phone, email)
            self._show_success_modal("Success", "Tenant updated")
            self.load_tenants()
            self.clear_fields()
            return

        try:
            TenantController.add_tenant(name, ni_number, phone, email)
        except Exception as exc:
            messagebox.showerror("Error", f"Unable to add tenant: {exc}")
            return

        self._show_success_modal("Success", "Tenant registered")

        self.load_tenants()
        self.clear_fields()

    def delete_tenant(self):
        if not self.can_manage_tenants:
            messagebox.showwarning("Read-only Access", "Your role can view tenant records but cannot modify them.")
            return
        if not self.selected_tenant_id:
            messagebox.showerror("Error", "Please select a tenant card first")
            return

        confirm = messagebox.askyesno("Confirm", "Delete this tenant record?")
        if not confirm:
            return

        TenantController.delete_tenant(self.selected_tenant_id)
        messagebox.showinfo("Success", "Tenant deleted")

        self.load_tenants()
        self.clear_fields()

    def clear_fields(self):
        self.selected_tenant_id = None
        self.current_edit_tenant = None

        for entry in [self.name, self.NI_number, self.phone, self.email, self.occupation, self.reference]:
            entry.delete(0, tk.END)

        self._refresh_placeholders()

        self.form_title.configure(text="Register New Tenant")
        self.primary_btn.configure(text="Register Tenant")
        if self.delete_btn.winfo_manager():
            self.delete_btn.pack_forget()

    def _refresh_placeholders(self):
        # Re-apply placeholders so they are visible immediately after reset.
        self.name.configure(placeholder_text="e.g. John Smith")
        self.NI_number.configure(placeholder_text="AB123456C")
        self.phone.configure(placeholder_text="07700000000")
        self.email.configure(placeholder_text="john@gmail.com")
        self.occupation.configure(placeholder_text="e.g. Teacher")
        self.reference.configure(placeholder_text="Employer / previous landlord")

    def _display_status(self, tenant):
        raw_status = str(tenant.get("lease_status", "No Lease")).strip().lower()
        end_date = self._parse_date(tenant.get("end_date"))

        if raw_status == "active":
            if end_date:
                days_left = (end_date - date.today()).days
                if days_left <= 60:
                    return "Expiring Soon"
            return "Active"

        if raw_status in {"ended", "notice given"}:
            return "Notice Given"

        return "New"

    def _unit_text(self, tenant):
        apt_id = tenant.get("apartmentID")
        city = tenant.get("city") or self.city_scope or "Unassigned"

        if not apt_id:
            return f"No unit assigned · {city}"

        return f"Unit #{apt_id} · {city}"

    def _reference_text(self, tenant):
        if tenant.get("email"):
            return "Email on file"
        return "Not provided"

    def _format_period(self, start_date, end_date):
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)

        if not start and not end:
            return "Not assigned"

        start_label = start.strftime("%b %Y") if start else "-"
        end_label = end.strftime("%b %Y") if end else "-"
        return f"{start_label} - {end_label}"

    def _format_rent(self, value):
        try:
            return f"£{float(value):,.0f}"
        except Exception:
            return "-"

    def _format_notice_date(self, end_date):
        parsed = self._parse_date(end_date)
        if not parsed:
            return "-"
        return parsed.strftime("%b %d, %Y")

    def _parse_date(self, value):
        if not value:
            return None

        value = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _to_ddmmyyyy(self, value):
        parsed = self._parse_date(value)
        if not parsed:
            return ""
        return parsed.strftime("%d/%m/%Y")
