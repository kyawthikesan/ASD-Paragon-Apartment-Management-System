import os
from datetime import datetime
import tkinter as tk

import customtkinter as ctk

from controllers.auth_controller import AuthController

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False


ctk.set_appearance_mode("light")


class PremiumAppShell(ctk.CTkFrame):
    """Shared CustomTkinter scaffold for dashboard-style screens."""

    SIDEBAR_BG = "#18150F"
    BODY_BG = "#F8F5F0"
    CARD_BG = "#FFFFFF"
    GOLD = "#C9A84C"
    GOLD_HOVER = "#D4B465"
    GOLD_SOFT = "#F0E5CF"
    TEXT_DARK = "#241D12"
    TEXT_MID = "#6B5D44"
    TEXT_SOFT = "#9A8A70"
    BORDER = "#E5DAC8"
    SEARCH_BG = "#F3EEE5"
    ACTIVE_BG = "#2B2417"
    DIVIDER = "#332C20"
    SIDEBAR_ICON_LIGHT = (242, 232, 210)

    def __init__(
        self,
        parent,
        page_title,
        on_logout,
        active_nav=None,
        nav_items=None,
        nav_sections=None,
        footer_action_label="Logout",
        search_placeholder="Search...",
        location_label=None,
        on_search_change=None,
        on_search_submit=None,
        on_bell_click=None,
        on_settings_click=None,
        notification_count=0,
    ):
        super().__init__(parent, fg_color=self.BODY_BG, corner_radius=0)
        self.pack(fill="both", expand=True)

        user = AuthController.current_user
        self._full_name = self._read_user_value(user, "full_name", "Unknown User")
        role_name = self._read_user_value(user, "role_name", "staff")
        self._role_key = str(role_name).strip().lower()
        self._role_name = str(role_name).replace("_", " ").title()
        self._display_name = " ".join(str(self._full_name).split()).title() or "Unknown User"

        self._search_placeholder = search_placeholder
        self._location_label = self._resolve_location_label(location_label, user)
        self._on_search_change = on_search_change
        self._on_search_submit = on_search_submit
        self._on_bell_click = on_bell_click
        self._on_settings_click = on_settings_click
        self._notification_count = notification_count

        self._brand_image = None
        self._icon_cache = {}

        if nav_sections is None:
            nav_sections = [{"title": "Overview", "items": nav_items or []}]

        self._build_layout(page_title, on_logout, active_nav, nav_sections, footer_action_label)

    @staticmethod
    def _read_user_value(user, key, fallback):
        if user is None:
            return fallback
        try:
            return user[key]
        except Exception:
            return fallback

    def _build_layout(self, page_title, on_logout, active_nav, nav_sections, footer_action_label):
        # Main shell container
        frame = ctk.CTkFrame(self, fg_color=self.BODY_BG, corner_radius=0)
        frame.pack(fill="both", expand=True)

        # Sidebar column fixed, body column expandable
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=1)

        sidebar = ctk.CTkFrame(
            frame,
            fg_color=self.SIDEBAR_BG,
            corner_radius=0,
            width=230,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        body = ctk.CTkFrame(frame, fg_color=self.BODY_BG, corner_radius=0)
        body.grid(row=0, column=1, sticky="nsew")
        body.grid_rowconfigure(1, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._build_sidebar(sidebar, on_logout, active_nav, nav_sections, footer_action_label)
        self._build_topbar(body, page_title)

        self.content = ctk.CTkFrame(body, fg_color=self.BODY_BG, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew", padx=22, pady=(8, 16))
        self.content.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self, sidebar, on_logout, active_nav, nav_sections, footer_action_label):
        # Sidebar grid structure:
        # 0 = brand
        # 1 = location
        # 2 = nav area
        # 3 = footer
        sidebar.grid_rowconfigure(0, weight=0)
        sidebar.grid_rowconfigure(1, weight=0)
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_rowconfigure(3, weight=0)
        sidebar.grid_columnconfigure(0, weight=1)

        # ---------------- Brand ----------------
        top = ctk.CTkFrame(sidebar, fg_color=self.SIDEBAR_BG, corner_radius=0)
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(24, 12))
        self._render_brand(top)

        # ---------------- Location (hidden for admin to save vertical space) ----------------
        if self._role_key != "admin":
            location_box = ctk.CTkFrame(sidebar, fg_color=self.SIDEBAR_BG, corner_radius=0)
            location_box.grid(row=1, column=0, sticky="ew", padx=18, pady=(8, 18))
            self._render_location_row(location_box)

        # ---------------- Navigation ----------------
        nav_wrap = ctk.CTkFrame(sidebar, fg_color=self.SIDEBAR_BG, corner_radius=0)
        nav_wrap.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 0))
        nav_wrap.grid_columnconfigure(0, weight=1)

        nav_content = ctk.CTkFrame(
            nav_wrap,
            fg_color=self.SIDEBAR_BG,
            corner_radius=0,
        )
        nav_content.grid(row=0, column=0, sticky="nsew")

        for section in nav_sections:
            title = section.get("title", "").upper()
            items = section.get("items", [])

            if title:
                ctk.CTkLabel(
                    nav_content,
                    text=title,
                    text_color="#8F7F63",
                    font=("Arial", 11, "bold"),
                    anchor="w",
                    height=18,
                ).pack(fill="x", padx=14, pady=(14, 8))

            for item in items:
                if isinstance(item, tuple):
                    label, action = item
                    icon_key, badge = None, None
                else:
                    label = item.get("label", "")
                    action = item.get("action")
                    icon_key = item.get("icon")
                    badge = item.get("badge")

                is_active = label == active_nav

                row = ctk.CTkFrame(
                    nav_content,
                    fg_color=self.ACTIVE_BG if is_active else "transparent",
                    corner_radius=14 if is_active else 0,
                    height=40,
                )
                row.pack(fill="x", padx=8, pady=4)
                row.pack_propagate(False)

                btn = ctk.CTkButton(
                    row,
                    text=label,
                    command=action,
                    fg_color="transparent",
                    hover_color="#241F16",
                    text_color=self.GOLD if is_active else "#F2E8D2",
                    anchor="w",
                    corner_radius=14,
                    height=40,
                    font=("Arial", 13, "bold" if is_active else "normal"),
                )
                btn.pack(side="left", fill="both", expand=True, padx=(14, 12))

                icon_image = self._load_icon(
                    icon_key,
                    size=(18, 18),
                    tint=self.GOLD if is_active else "#F2E8D2",
                )
                if icon_image:
                    btn.configure(image=icon_image, compound="left")
                    btn._icon_ref = icon_image
                else:
                    fallback = self._fallback_icon(label)
                    btn.configure(text=f"  {fallback}  {label}")

                if badge is not None:
                    ctk.CTkLabel(
                        row,
                        text=str(badge),
                        text_color=self.TEXT_DARK,
                        fg_color=self.GOLD,
                        corner_radius=10,
                        width=24,
                        height=20,
                        font=("Arial", 10, "bold"),
                    ).pack(side="right", padx=(0, 12), pady=10)

        # ---------------- Footer ----------------
        footer = ctk.CTkFrame(sidebar, fg_color=self.SIDEBAR_BG, corner_radius=0)
        footer.grid(row=3, column=0, sticky="ew", padx=14, pady=(8, 10))

        ctk.CTkFrame(
            footer,
            fg_color=self.DIVIDER,
            corner_radius=0,
            height=1,
        ).pack(fill="x", pady=(8, 12))

        initials = "".join(part[0] for part in self._display_name.split()[:2]).upper() or "U"

        profile_row = ctk.CTkFrame(footer, fg_color=self.SIDEBAR_BG, corner_radius=0)
        profile_row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            profile_row,
            text=initials,
            text_color=self.TEXT_DARK,
            fg_color=self.GOLD,
            width=44,
            height=44,
            corner_radius=22,
            font=("Arial", 16, "bold"),
        ).pack(side="left", padx=(0, 10))

        text_col = ctk.CTkFrame(profile_row, fg_color=self.SIDEBAR_BG, corner_radius=0)
        text_col.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            text_col,
            text=self._display_name,
            text_color="#F6EEDC",
            font=("Arial", 12, "bold"),
            anchor="w",
            justify="left",
            height=20,
        ).pack(fill="x")

        ctk.CTkLabel(
            text_col,
            text=self._role_name,
            text_color=self.TEXT_SOFT,
            font=("Arial", 10),
            anchor="w",
            justify="left",
            height=18,
        ).pack(fill="x")

        ctk.CTkFrame(
            footer,
            fg_color=self.DIVIDER,
            corner_radius=0,
            height=1,
        ).pack(fill="x", pady=(0, 4))

        logout_row = ctk.CTkFrame(
            footer,
            fg_color="transparent",
            corner_radius=12,
            height=40,
        )
        logout_row.pack(fill="x", pady=(0, 2))
        logout_row.pack_propagate(False)

        logout_btn = ctk.CTkButton(
            logout_row,
            text=footer_action_label,
            command=on_logout,
            fg_color="transparent",
            hover_color="#241F16",
            text_color="#F2E8D2",
            anchor="w",
            corner_radius=12,
            height=40,
            font=("Arial", 13, "bold"),
        )
        logout_btn.pack(fill="both", expand=True, padx=10)

        logout_icon = self._load_icon("logout", size=(18, 18), tint="#F2E8D2")
        if logout_icon:
            logout_btn.configure(image=logout_icon, compound="left")
            logout_btn._icon_ref = logout_icon
        else:
            logout_btn.configure(text=f"  ↪  {footer_action_label}")

    def _build_topbar(self, body, page_title):
        topbar = ctk.CTkFrame(body, fg_color=self.BODY_BG, corner_radius=0, height=72)
        topbar.grid(row=0, column=0, sticky="ew", padx=0, pady=(8, 0))
        topbar.grid_columnconfigure(0, weight=1)
        topbar.grid_columnconfigure(1, weight=1)
        topbar.grid_propagate(False)

        ctk.CTkLabel(
            topbar,
            text=page_title,
            text_color=self.TEXT_DARK,
            font=("Georgia", 24, "bold"),
            height=30,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(12, 8))

        right = ctk.CTkFrame(topbar, fg_color=self.BODY_BG, corner_radius=0)
        right.grid(row=0, column=1, sticky="e", padx=18, pady=(10, 4))

        search_wrap = ctk.CTkFrame(
            right,
            fg_color=self.SEARCH_BG,
            bg_color=self.BODY_BG,
            corner_radius=22,
            border_width=1,
            border_color="#D8CAB0",
            width=320,
            height=38,
        )
        search_wrap.pack(side="left", padx=(0, 12))
        search_wrap.pack_propagate(False)

        search_inner = ctk.CTkFrame(
            search_wrap,
            fg_color="transparent",
            bg_color="transparent",
            corner_radius=0,
        )
        search_inner.pack(fill="both", expand=True, padx=12, pady=4)

        search_icon = self._load_icon("search", size=(16, 16), tint=self.TEXT_MID)
        if search_icon:
            ctk.CTkLabel(
                search_inner,
                text="",
                image=search_icon,
                fg_color="transparent",
                text_color=self.TEXT_MID,
            ).pack(side="left", padx=(2, 8))
        else:
            ctk.CTkLabel(
                search_inner,
                text="⌕",
                text_color=self.TEXT_MID,
                font=("Arial", 14, "bold"),
                fg_color="transparent",
            ).pack(side="left", padx=(2, 8))

        self.search_entry = ctk.CTkEntry(
            search_inner,
            fg_color="transparent",
            bg_color="transparent",
            border_width=0,
            text_color=self.TEXT_MID,
            placeholder_text=self._search_placeholder,
            placeholder_text_color="#8B857C",
            corner_radius=0,
            width=250,
            height=26,
            font=("Arial", 12),
        )
        self.search_entry.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.search_entry.bind("<KeyRelease>", self._handle_search_change)
        self.search_entry.bind("<Return>", self._handle_search_submit)

        bell_btn = self._icon_pill_button(right, "bell", self._handle_bell_click, fallback="🔔")
        bell_btn.pack(side="left", padx=(0, 10))

        if self._notification_count > 0:
            ctk.CTkLabel(
                bell_btn,
                text=str(self._notification_count),
                text_color=self.TEXT_DARK,
                fg_color=self.GOLD,
                corner_radius=8,
                font=("Arial", 8, "bold"),
                width=16,
                height=16,
            ).place(relx=1.0, rely=0.0, x=-2, y=2, anchor="ne")

        settings_btn = self._icon_pill_button(right, "settings", self._handle_settings_click, fallback="⚙️")
        settings_btn.pack(side="left", padx=(0, 12))

        self.date_label = ctk.CTkLabel(
            right,
            text=datetime.now().strftime("%a %d %b %Y"),
            text_color=self.TEXT_MID,
            fg_color=self.SEARCH_BG,
            bg_color=self.BODY_BG,
            corner_radius=16,
            width=138,
            height=38,
            font=("Arial", 11, "bold"),
            anchor="center",
        )
        self.date_label.pack(side="left")
        self._refresh_date()

    def _icon_pill_button(self, parent, icon_key, command, fallback="•"):
        btn = ctk.CTkButton(
            parent,
            text="",
            command=command,
            fg_color=self.SEARCH_BG,
            hover_color="#E9DECF",
            bg_color=self.BODY_BG,
            text_color=self.TEXT_MID,
            width=38,
            height=38,
            corner_radius=16,
            border_width=0,
        )

        icon_image = self._load_icon(icon_key, size=(18, 18), tint="#7A6F5D")
        if icon_image:
            btn.configure(image=icon_image, text="")
            btn._icon_ref = icon_image
        else:
            btn.configure(text=fallback, font=("Arial", 14))

        return btn

    def _render_brand(self, parent):
        logo_candidates = [
            os.path.join("images", "paragon.png"),
            os.path.join("images", "logo.png"),
            os.path.join("images", "paragon_logo.png"),
        ]

        for logo_path in logo_candidates:
            if os.path.exists(logo_path):
                try:
                    if PIL_AVAILABLE:
                        image = Image.open(logo_path).convert("RGBA")
                        image = self._trim_logo_image(image)
                        target_width = 140
                        ratio = target_width / max(1, image.width)
                        target_size = (target_width, max(1, int(image.height * ratio)))
                        image = image.resize(target_size, Image.LANCZOS)
                        self._brand_image = ImageTk.PhotoImage(image)
                    else:
                        self._brand_image = tk.PhotoImage(file=logo_path)

                    tk.Label(parent, image=self._brand_image, bg=self.SIDEBAR_BG).pack(anchor="center", pady=(0, 6))
                    return
                except Exception:
                    pass

        ctk.CTkLabel(
            parent,
            text="PARAGON",
            text_color=self.GOLD,
            font=("Georgia", 28, "bold"),
            anchor="w",
            height=34,
        ).pack(fill="x", pady=(0, 3))

        ctk.CTkLabel(
            parent,
            text="PROPERTY MANAGEMENT",
            text_color="#F1E7D2",
            font=("Arial", 10, "bold"),
            anchor="w",
            height=16,
        ).pack(fill="x")

    def _render_location_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color=self.SIDEBAR_BG, corner_radius=0)
        row.pack(fill="x")

        location_pill = ctk.CTkFrame(
            row,
            fg_color="#2B2417",
            corner_radius=16,
            border_width=1,
            border_color="#5A4520",
            height=42,
        )
        location_pill.pack(fill="x")
        location_pill.pack_propagate(False)

        inner = ctk.CTkFrame(location_pill, fg_color="transparent", corner_radius=0)
        inner.pack(fill="both", expand=True, padx=14, pady=6)

        ctk.CTkLabel(
            inner,
            text="📍",
            text_color=self.GOLD,
            font=("Arial", 13),
            width=18,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            inner,
            text=self._location_label,
            text_color="#F0E4CA",
            font=("Arial", 12, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

    def _load_icon(self, icon_key, size=(18, 18), tint=None):
        if not icon_key or not PIL_AVAILABLE:
            return None

        tint_rgb = self._to_rgb_tuple(tint) if tint else None
        tint_key = tint_rgb if tint_rgb else "original"
        cache_key = f"{icon_key}_{size[0]}x{size[1]}_{tint_key}"

        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        possible_files = [
            os.path.join("images", "icons", f"{icon_key}.png"),
            os.path.join("images", "icons", f"{icon_key}.jpg"),
            os.path.join("images", "icons", f"{icon_key}.jpeg"),
        ]

        for path in possible_files:
            if os.path.exists(path):
                try:
                    image = Image.open(path).convert("RGBA")
                    image = self._trim_logo_image(image)

                    if tint_rgb:
                        image = self._tint_icon(image, tint_rgb)

                    ctk_image = ctk.CTkImage(
                        light_image=image,
                        dark_image=image,
                        size=size
                    )
                    self._icon_cache[cache_key] = ctk_image
                    return ctk_image
                except Exception:
                    return None

        return None
    
    def _load_local_modal_icon(self, icon_name, size=(34, 34)):
        """
        Load a local icon image for modal windows.
        Returns a PhotoImage if found, otherwise None.
        """
        if not PIL_AVAILABLE:
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
                    image = self._trim_logo_image(image)
                    image = image.resize(size, Image.LANCZOS)
                    return ImageTk.PhotoImage(image)
                except Exception:
                    return None

        return None

    def _tint_icon(self, image, rgb):
        pixels = image.getdata()
        recolored = []

        for r, g, b, a in pixels:
            if a == 0:
                recolored.append((r, g, b, a))
            else:
                recolored.append((rgb[0], rgb[1], rgb[2], a))

        image.putdata(recolored)
        return image

    def _to_rgb_tuple(self, color):
        if isinstance(color, tuple) and len(color) == 3:
            return color

        if isinstance(color, str) and color.startswith("#") and len(color) == 7:
            return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))

        return self.SIDEBAR_ICON_LIGHT

    def _fallback_icon(self, label):
        mapping = {
            "Dashboard": "⌂",
            "Tenants": "👤",
            "Apartments": "▦",
            "Leases": "◫",
            "Payments": "£",
            "Reports": "▥",
            "User Access": "◌",
        }
        return mapping.get(label, "•")

    def show_premium_info_modal(
        self,
        title: str,
        rows: list,
        icon_text: str = "ℹ",
        icon_fg: str = "#B8891F",
        icon_bg: str = "#F6EED7",
        button_text: str = "OK",
        on_close=None,
        highlight_nonzero=False,
        icon_image_name=None,
        icon_image_size=(28, 28),
    ):

        # Reusable premium modal for Alerts / Account Settings / other info popups.

        root = self.winfo_toplevel()

        # ---------------------------------------------------------
        # Get current root window position and size
        # so the modal can appear centered on top of it
        # ---------------------------------------------------------
        root.update_idletasks()
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()

        width = 620
        height = 460

        # Final centered position of the popup
        final_x = x + (w // 2) - (width // 2)
        final_y = y + (h // 2) - (height // 2)

        # Start slightly lower for a smooth slide-up animation
        start_y = final_y + 18

        # ---------------------------------------------------------
        # Create the popup window
        # overrideredirect(True) removes the OS title bar
        # ---------------------------------------------------------
        modal = tk.Toplevel(root)
        modal.overrideredirect(True)
        modal.configure(bg="#000000")
        modal.geometry(f"{width}x{height}+{final_x}+{start_y}")

        # Start transparent for fade-in animation
        try:
            modal.attributes("-alpha", 0.0)
        except Exception:
            pass

        # ---------------------------------------------------------
        # Final cleanup when modal closes
        # ---------------------------------------------------------
        def finish_close():
            try:
                modal.grab_release()
            except Exception:
                pass

            try:
                modal.destroy()
            except Exception:
                pass

            if callable(on_close):
                try:
                    on_close()
                except Exception:
                    pass

        # ---------------------------------------------------------
        # Fade out + slide down animation
        # ---------------------------------------------------------
        def fade_out(alpha=1.0, current_y=None):
            if current_y is None:
                current_y = modal.winfo_y()

            alpha -= 0.10
            current_y += 2

            if alpha <= 0:
                finish_close()
                return

            try:
                modal.attributes("-alpha", alpha)
            except Exception:
                pass

            modal.geometry(f"{width}x{height}+{final_x}+{current_y}")
            modal.after(16, lambda: fade_out(alpha, current_y))

        # Button / ESC close handler
        def close_modal():
            fade_out()

        # ---------------------------------------------------------
        # Outer dark shadow layer
        # ---------------------------------------------------------
        shadow = ctk.CTkFrame(
            modal,
            fg_color="#000000",
            corner_radius=28
        )
        shadow.pack(fill="both", expand=True)

        # ---------------------------------------------------------
        # Main popup card
        # ---------------------------------------------------------
        card = ctk.CTkFrame(
            shadow,
            fg_color="#F7F7FA",
            corner_radius=28,
        )
        card.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.965,
            relheight=0.965
        )

        # Small top spacer
        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()

        # Icon circle
        icon_circle = ctk.CTkFrame(
            card,
            width=84,
            height=84,
            corner_radius=42,
            fg_color=icon_bg
        )
        icon_circle.pack(pady=(8, 6))
        icon_circle.pack_propagate(False)

        # Try to add custom image icon first
        icon_widget_added = False
        if icon_image_name:
            icon_image = self._load_local_modal_icon(icon_image_name, size=icon_image_size)
            if icon_image:
                icon_label = tk.Label(
                    icon_circle,
                    image=icon_image,
                    bg=icon_bg,
                    bd=0,
                    highlightthickness=0
                )
                icon_label.image = icon_image
                icon_label.pack(expand=True)
                icon_widget_added = True

        # Fallback to text icon if image icon is not available
        if not icon_widget_added:
            tk.Label(
                icon_circle,
                text=icon_text,
                bg=icon_bg,
                fg=icon_fg,
                font=("Arial", 22),
                bd=0,
                highlightthickness=0
            ).pack(expand=True)

        # ---------------------------------------------------------
        # Modal title
        # Slightly smaller so it fits better with row content
        # ---------------------------------------------------------
        ctk.CTkLabel(
            card,
            text=title,
            text_color="#2E2418",
            font=("Arial", 20, "bold"),
            justify="center"
        ).pack(pady=(10, 8))

        # ---------------------------------------------------------
        # Content area for rows
        # Tighter padding so bottom content stays visible
        # ---------------------------------------------------------
        content_wrap = ctk.CTkFrame(card, fg_color="transparent")
        content_wrap.pack(fill="both", expand=True, padx=55, pady=(0, 6))

        # Build each info row
        for label_text, value_text in rows:
            row_card = ctk.CTkFrame(
                content_wrap,
                fg_color="#F1ECE3",
                corner_radius=18,
                border_width=1,
                border_color="#E1D6C5",
                height=42
            )
            row_card.pack(fill="x", pady=5)
            row_card.pack_propagate(False)

            inner = ctk.CTkFrame(row_card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=16, pady=4)

            # Make left side expand, right side stay compact
            inner.grid_columnconfigure(0, weight=1)
            inner.grid_columnconfigure(1, weight=0)

            # Default value color
            value_color = "#6D5C43"

            # Optional: highlight numeric values above zero in red
            if highlight_nonzero:
                try:
                    if float(value_text) > 0:
                        value_color = "#B03A2E"
                except Exception:
                    pass

            # Left label
            ctk.CTkLabel(
                inner,
                text=label_text,
                text_color="#8A7758",
                font=("Arial", 11, "bold"),
                anchor="w"
            ).grid(row=0, column=0, sticky="w")

            # Right value
            ctk.CTkLabel(
                inner,
                text=str(value_text),
                text_color=value_color,
                font=("Arial", 15, "bold"),
                anchor="e"
            ).grid(row=0, column=1, sticky="e")

        # ---------------------------------------------------------
        # OK button
        # SAME size as the access denied popup button
        # ---------------------------------------------------------
        ctk.CTkButton(
            card,
            text=button_text,
            command=close_modal,
            fg_color="#CDAA45",
            hover_color="#B89232",
            text_color="#2A2115",
            corner_radius=22,
            font=("Arial", 18, "bold"),
            height=50,
            width=260
        ).pack(pady=(6, 14))

        # ESC key also closes the popup
        modal.bind("<Escape>", lambda e: close_modal())

        # Bring modal to front and lock focus to it
        modal.lift()
        modal.focus_force()
        modal.grab_set()

        # ---------------------------------------------------------
        # Fade in + slide up animation
        # ---------------------------------------------------------
        def fade_in(alpha=0.0, current_y=None):
            if current_y is None:
                current_y = start_y

            alpha += 0.10
            next_y = current_y - 2

            if alpha >= 1.0:
                alpha = 1.0
                next_y = final_y

            try:
                modal.attributes("-alpha", alpha)
            except Exception:
                pass

            modal.geometry(f"{width}x{height}+{final_x}+{next_y}")

            if alpha < 1.0:
                modal.after(16, lambda: fade_in(alpha, next_y))

        # Start animation
        fade_in()

    @staticmethod
    def _trim_logo_image(image):
        alpha = image.split()[3]
        alpha_mask = alpha.point(lambda p: 255 if p > 6 else 0)
        bbox = alpha_mask.getbbox()
        if bbox:
            image = image.crop(bbox)
        return image

    def _resolve_location_label(self, location_label, user):
        if location_label:
            cleaned = str(location_label).strip()
        else:
            cleaned = str(self._read_user_value(user, "location", "")).strip()

        if not cleaned or cleaned.lower() in {"none", "null", "n/a"}:
            return "No Assigned Location"
        if cleaned.lower() in {"all cities", "all locations"}:
            return "All Cities"
        if cleaned.lower().endswith("office"):
            return cleaned
        return f"{cleaned} Office"

    def _refresh_date(self):
        self.date_label.configure(text=datetime.now().strftime("%a %d %b %Y"))
        self.after(60000, self._refresh_date)

    def _handle_search_change(self, event=None):
        if callable(self._on_search_change):
            self._on_search_change((self.search_entry.get() or "").strip())

    def _handle_search_submit(self, event=None):
        if callable(self._on_search_submit):
            self._on_search_submit((self.search_entry.get() or "").strip())

    def _handle_bell_click(self):
        if callable(self._on_bell_click):
            self._on_bell_click()
    def _handle_settings_click(self):
        if callable(self._on_settings_click):
            self._on_settings_click()
