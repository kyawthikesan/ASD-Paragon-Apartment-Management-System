import os
import tkinter as tk
from tkinter import messagebox
from io import BytesIO
import sys
from controllers.auth_controller import AuthController
from styles.colors import *
from styles.fonts import *

try:
    from PIL import Image, ImageTk, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except Exception:
    CAIROSVG_AVAILABLE = False


class LoginView(tk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=BG_MAIN)

        self.parent = parent
        self.on_login_success = on_login_success
        self.logo_image = None
        self.remember_var = tk.BooleanVar(value=False)
        self.show_password = False
        self.password_placeholder_active = True
        self.username_placeholder_active = True
        self.ui_cursor = "pointinghand" if sys.platform == "darwin" else "hand2"
        self.eye_icon_show = {}
        self.eye_icon_hide = {}
        self.using_svg_eye_icons = False

        self._load_password_toggle_icons()

        self.pack(fill="both", expand=True)
        self._build_ui()
        self._load_remembered_username()

    # ── Layout ─────────────────────────────────────────────
    def _build_ui(self):
        self.left = tk.Frame(self, bg=LEFT_BG, width=360)
        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)

        self.right = tk.Frame(self, bg=BG_MAIN)
        self.right.pack(side="right", fill="both", expand=True)

        self._build_left_panel(self.left)
        self._build_right_panel(self.right)

    # ── Left panel ─────────────────────────────────────────
    def _build_left_panel(self, parent):
        tk.Frame(parent, bg=LEFT_BORDER, width=1).place(
            relx=1.0, rely=0, relheight=1.0, anchor="ne"
        )

        self._load_logo(parent)

        tk.Frame(parent, bg=DIVIDER_LITE, height=1, width=150).place(
            relx=0.5, rely=0.48, anchor="center"
        )

        tk.Label(
            parent,
            text="OUR LOCATIONS",
            bg=LEFT_BG,
            fg=TAUPE_MID,
            font=("Segoe UI", 7, "bold"),
        ).place(relx=0.5, rely=0.54, anchor="center")

        cities = ["Bristol", "Cardiff", "London", "Manchester"]
        for i, city in enumerate(cities):
            tk.Label(
                parent,
                text=city,
                bg=LEFT_BG,
                fg=TAUPE_DARK,
                font=FONT_CITY,
            ).place(relx=0.5, rely=0.60 + i * 0.065, anchor="center")

        tk.Label(
            parent,
            text="Secure  ·  Scalable  ·  Trusted",
            bg=LEFT_BG,
            fg=TAUPE_LIGHT,
            font=("Segoe UI", 7),
        ).place(relx=0.5, rely=0.94, anchor="center")

    def _load_logo(self, parent):
        logo_path = os.path.join("images", "logo.png")

        if os.path.exists(logo_path) and PIL_AVAILABLE:
            try:
                image = Image.open(logo_path).convert("RGBA")
                image = self._trim_logo_alpha_content(image)

                target_w = min(300, image.width)
                ratio = target_w / image.width
                target_h = max(1, int(image.height * ratio))
                if image.width != target_w:
                    image = image.resize((target_w, target_h), Image.LANCZOS)

                image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=145, threshold=2))

                self.logo_image = ImageTk.PhotoImage(image)
                tk.Label(parent, image=self.logo_image, bg=LEFT_BG).place(
                    relx=0.5, rely=0.285, anchor="center"
                )
                return
            except Exception:
                pass

        tk.Label(
            parent,
            text="PARAGON",
            bg=LEFT_BG,
            fg=TAUPE_DARK,
            font=FONT_BRAND,
        ).place(relx=0.5, rely=0.25, anchor="center")

    def _trim_logo_alpha_content(self, image):
        alpha = image.split()[3]
        # Ignore tiny alpha noise at edges; keep only real logo pixels.
        mask = alpha.point(lambda p: 255 if p > 8 else 0)
        bbox = mask.getbbox()
        if bbox:
            return image.crop(bbox)
        return image

    # ── Right panel ────────────────────────────────────────
    def _build_right_panel(self, parent):
        self.right_backdrop = tk.Canvas(
            parent,
            bg=BG_MAIN,
            highlightthickness=0,
            bd=0,
        )
        self.right_backdrop.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.right_backdrop.bind("<Configure>", self._draw_right_backdrop)

        shadow = tk.Frame(parent, bg="#0E0C0A")
        shadow.place(relx=0.5, rely=0.5, anchor="center", width=532, height=572)

        shell = tk.Frame(parent, bg=BG_MAIN)
        shell.place(relx=0.5, rely=0.5, anchor="center", width=520, height=560)

        panel = tk.Frame(
            shell,
            bg=BG_MAIN,
            highlightthickness=1,
            highlightbackground="#2A2520",
        )
        panel.pack(fill="both", expand=True)

        tk.Frame(panel, bg=METAL, height=3).pack(fill="x")

        content = tk.Frame(panel, bg=BG_MAIN)
        content.pack(fill="both", expand=True, padx=56, pady=48)

        # Header
        tk.Label(
            content,
            text="Welcome back",
            bg=BG_MAIN,
            fg=TEXT_ON_DARK,
            font=FONT_HEADING,
        ).pack(anchor="w")

        tk.Label(
            content,
            text="Sign in to continue to PAMS",
            bg=BG_MAIN,
            fg=TEXT_MUTED,
            font=FONT_SUBHEAD,
        ).pack(anchor="w", pady=(4, 0))

        tk.Frame(content, bg=DIVIDER_DARK, height=1).pack(fill="x", pady=30)

        self.username_wrap, self.username_entry = self._field(content)
        self.username_wrap.pack(fill="x", pady=(0, 20))
        self._set_username_placeholder()

        # ── Password ──
        self.password_wrap = tk.Frame(
            content,
            bg=FIELD_BG,
            highlightthickness=1,
            highlightbackground=FIELD_BORDER,
            highlightcolor=METAL,
        )
        self.password_wrap.pack(fill="x", pady=(6, 0))
        self.password_wrap.grid_columnconfigure(0, weight=1)

        self.password_entry = tk.Entry(
            self.password_wrap,
            font=FONT_INPUT,
            bg=FIELD_BG,
            fg=TEXT_MUTED,
            relief="flat",
            bd=0,
            highlightthickness=0,
            insertbackground=METAL,
        )
        self.password_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            ipady=12,
            padx=(14, 8),
        )

        self.eye_btn = tk.Canvas(
            self.password_wrap,
            width=26,
            height=20,
            bg=FIELD_BG,
            highlightthickness=0,
            cursor=self.ui_cursor,
        )
        self.eye_btn.grid(row=0, column=1, padx=(0, 10))
        self._render_password_toggle_icon()

        self._set_password_placeholder()
        self._focus_ring(self.password_entry, self.password_wrap)

        self.password_entry.bind("<FocusIn>", self._password_focus_in)
        self.password_entry.bind("<FocusOut>", self._password_focus_out)

        self.eye_btn.bind("<Button-1>", lambda e: self._toggle_password())
        self.eye_btn.bind("<Enter>", lambda e: self._render_password_toggle_icon(color=METAL_LIGHT))
        self.eye_btn.bind("<Leave>", lambda e: self._render_password_toggle_icon())

        # ── Remember ──
        row = tk.Frame(content, bg=BG_MAIN)
        row.pack(fill="x", pady=(16, 28))

        tk.Checkbutton(
            row,
            text="Remember me",
            variable=self.remember_var,
            bg=BG_MAIN,
            fg=TEXT_MUTED,
            activebackground=BG_MAIN,
            activeforeground=TEXT_ON_DARK,
            selectcolor=BG_MAIN,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=FONT_SMALL,
            cursor=self.ui_cursor,
        ).pack(side="left")

        # ── Button ──
        btn = tk.Button(
            content,
            text="SIGN IN",
            command=self._login,
            font=FONT_BTN,
            bg=METAL,
            fg=BTN_FG,
            activebackground=METAL_LIGHT,
            activeforeground=BTN_FG,
            relief="flat",
            bd=0,
            cursor=self.ui_cursor,
            height=2,
        )
        btn.pack(fill="x")

        btn.bind("<Enter>", lambda e: btn.config(bg=METAL_LIGHT))
        btn.bind("<Leave>", lambda e: btn.config(bg=METAL))

        # ── Forgot ──
        forgot = tk.Label(
            content,
            text="Forgot password?",
            bg=BG_MAIN,
            fg=TEXT_MUTED,
            font=FONT_LINK,
            cursor=self.ui_cursor,
        )
        forgot.pack(pady=(14, 0))
        forgot.bind("<Button-1>", self._forgot_password)
        forgot.bind("<Enter>", lambda e: forgot.config(fg=METAL_LIGHT))
        forgot.bind("<Leave>", lambda e: forgot.config(fg=TEXT_MUTED))

        # Footer
        tk.Label(
            content,
            text="PAMS  ·  Paragon Apartment Management Systems",
            bg=BG_MAIN,
            fg=TEXT_SUB,
            font=("Segoe UI", 7),
        ).pack(pady=(28, 0))

        self.username_entry.focus_set()
        self.username_entry.bind("<Return>", lambda e: self._login())
        self.password_entry.bind("<Return>", lambda e: self._login())

    def _draw_right_backdrop(self, event=None):
        canvas = self.right_backdrop
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        canvas.delete("all")
        canvas.create_rectangle(0, 0, width, height, fill=BG_MAIN, outline="")
        canvas.create_oval(
            -width * 0.30,
            -height * 0.20,
            width * 0.35,
            height * 0.55,
            outline="#2A2520",
            width=1,
        )
        canvas.create_oval(
            width * 0.45,
            height * 0.35,
            width * 1.25,
            height * 1.20,
            outline="#24201C",
            width=1,
        )
        canvas.create_line(
            width * 0.18,
            0,
            width * 0.18,
            height,
            fill="#201C18",
            width=1,
        )

    # ── Input system ───────────────────────────────────────
    def _field(self, parent):
        wrap = tk.Frame(
            parent,
            bg=FIELD_BG,
            highlightthickness=1,
            highlightbackground=FIELD_BORDER,
            highlightcolor=METAL,
        )

        entry = tk.Entry(
            wrap,
            font=FONT_INPUT,
            bg=FIELD_BG,
            fg=TEXT_ON_DARK,
            relief="flat",
            bd=0,
            highlightthickness=0,
            insertbackground=METAL,
        )
        entry.pack(fill="both", expand=True, ipady=12, padx=14)

        self._focus_ring(entry, wrap)
        return wrap, entry

    def _focus_ring(self, entry, frame):
        entry.bind("<FocusIn>", lambda e: frame.config(highlightbackground=METAL))
        entry.bind("<FocusOut>", lambda e: frame.config(highlightbackground=FIELD_BORDER))

    def _set_username_placeholder(self):
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, "Enter your username")
        self.username_entry.config(fg=TEXT_MUTED)
        self.username_placeholder_active = True

        self.username_entry.bind("<FocusIn>", self._username_focus_in)
        self.username_entry.bind("<FocusOut>", self._username_focus_out)

    def _username_focus_in(self, event=None):
        if self.username_placeholder_active:
            self.username_entry.delete(0, tk.END)
            self.username_entry.config(fg=TEXT_ON_DARK)
            self.username_placeholder_active = False

    def _username_focus_out(self, event=None):
        if not self.username_entry.get().strip():
            self._set_username_placeholder()

    def _set_password_placeholder(self):
        self.password_entry.delete(0, tk.END)
        self.password_entry.config(show="", fg=TEXT_MUTED)
        self.password_entry.insert(0, "Enter your password")
        self.show_password = False
        self._render_password_toggle_icon()
        self.password_placeholder_active = True

    def _password_focus_in(self, event=None):
        if self.password_placeholder_active:
            self.password_entry.delete(0, tk.END)
            self.password_entry.config(
                fg=TEXT_ON_DARK,
                show="" if self.show_password else "•"
            )
            self.password_placeholder_active = False

    def _password_focus_out(self, event=None):
        if not self.password_entry.get():
            self._set_password_placeholder()

    # ── Logic ──────────────────────────────────────────────
    def _toggle_password(self):
        if self.password_placeholder_active:
            return

        self.show_password = not self.show_password

        if self.show_password:
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="•")
        self._render_password_toggle_icon()

    def _render_password_toggle_icon(self, color=None):
        if self.using_svg_eye_icons:
            state = "hide" if self.show_password else "show"
            shade = "hover" if color else "normal"
            icon_pack = self.eye_icon_hide if state == "hide" else self.eye_icon_show
            icon = icon_pack.get(shade) or icon_pack.get("normal")
            if icon:
                self.eye_btn.delete("all")
                self.eye_btn.create_image(13, 10, image=icon, anchor="center")
                return

        stroke = color or TEXT_MUTED
        self.eye_btn.delete("all")

        # Eye outline
        self.eye_btn.create_oval(4, 6, 22, 14, outline=stroke, width=2)
        self.eye_btn.create_oval(11, 8, 15, 12, outline=stroke, fill=stroke, width=1)

        # Strikethrough when password is hidden (eye-off)
        if not self.show_password:
            self.eye_btn.create_line(5, 15, 21, 5, fill=stroke, width=2)

    def _load_password_toggle_icons(self):
        if not (PIL_AVAILABLE and CAIROSVG_AVAILABLE):
            return

        eye_fill = self._resolve_icon_path("eye-fill.svg")
        eye_slash_fill = self._resolve_icon_path("eye-slash-fill.svg")
        if not eye_fill or not eye_slash_fill:
            return

        normal = TEXT_MUTED
        hover = METAL_LIGHT

        show_normal = self._build_tinted_svg_icon(eye_fill, normal)
        show_hover = self._build_tinted_svg_icon(eye_fill, hover)
        hide_normal = self._build_tinted_svg_icon(eye_slash_fill, normal)
        hide_hover = self._build_tinted_svg_icon(eye_slash_fill, hover)

        if not all([show_normal, show_hover, hide_normal, hide_hover]):
            return

        self.eye_icon_show = {"normal": show_normal, "hover": show_hover}
        self.eye_icon_hide = {"normal": hide_normal, "hover": hide_hover}
        self.using_svg_eye_icons = True

    def _resolve_icon_path(self, filename):
        candidates = [
            os.path.join("images", filename),
            os.path.expanduser(os.path.join("~", "Downloads", filename)),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _build_tinted_svg_icon(self, svg_path, color_hex):
        try:
            png_data = cairosvg.svg2png(url=svg_path, output_width=18, output_height=18)
            image = Image.open(BytesIO(png_data)).convert("RGBA")
            alpha = image.getchannel("A")
            colored = Image.new("RGBA", image.size, color_hex)
            colored.putalpha(alpha)
            return ImageTk.PhotoImage(colored)
        except Exception:
            return None

    def _load_remembered_username(self):
        if os.path.exists("remember_me.txt"):
            with open("remember_me.txt", "r") as f:
                saved = f.read().strip()

            if saved:
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, saved)
                self.username_entry.config(fg=TEXT_ON_DARK)
                self.username_placeholder_active = False
                self.remember_var.set(False)
            else:
                self.remember_var.set(False)
        else:
            self.remember_var.set(False)

    def _forgot_password(self, event=None):
        messagebox.showinfo(
            "Forgot Password",
            "Please contact your system administrator to reset your password."
        )

    def _login(self):
        username = "" if self.username_placeholder_active else self.username_entry.get().strip()
        password = "" if self.password_placeholder_active else self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Sign In Failed", "Please enter your username and password.")
            return

        success, message = AuthController.login(username, password)

        if success:
            if self.remember_var.get():
                with open("remember_me.txt", "w") as f:
                    f.write(username)
            elif os.path.exists("remember_me.txt"):
                os.remove("remember_me.txt")
            self.on_login_success(AuthController.get_current_role())
        else:
            messagebox.showerror("Sign In Failed", message)
