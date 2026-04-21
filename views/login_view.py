# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

import os
import tkinter as tk
import sys
from controllers.auth_controller import AuthController
from styles.colors import *
from styles.fonts import *

try:
    from PIL import Image, ImageTk, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class LoginView(tk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=BG_MAIN)

        self.parent = parent
        self.on_login_success = on_login_success

        # Keep references to images so Tkinter does not garbage collect them.
        self.logo_image = None
        self.forgot_icon_image = None
        self.signin_icon_image = None

        # Tracks whether the username should be saved locally.
        self.remember_var = tk.BooleanVar(value=False)

        # Used to switch between masked and visible password text.
        self.show_password = False

        # These flags help manage custom placeholder text behaviour.
        self.password_placeholder_active = True
        self.username_placeholder_active = True

        # macOS uses a different cursor name from Windows/Linux.
        self.ui_cursor = "pointinghand" if sys.platform == "darwin" else "hand2"

        # Stores password-eye icons for normal and hover states.
        self.eye_icon_show = {}
        self.eye_icon_hide = {}
        self.using_image_eye_icons = False
        self.eye_icon_size = (20, 20)

        self._load_password_toggle_icons()

        self.pack(fill="both", expand=True)
        self._build_ui()
        self._load_remembered_username()

    # Build the two main sections of the login screen.
    def _build_ui(self):
        self.left = tk.Frame(self, bg=LEFT_BG, width=360)
        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)

        self.right = tk.Frame(self, bg=BG_MAIN)
        self.right.pack(side="right", fill="both", expand=True)

        self._build_left_panel(self.left)
        self._build_right_panel(self.right)

    # Left side contains branding and location details.
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

    # Load the logo image if available; otherwise fall back to plain text branding.
    def _load_logo(self, parent):
        logo_path = os.path.join("images", "logo.png")

        if os.path.exists(logo_path) and PIL_AVAILABLE:
            try:
                image = Image.open(logo_path).convert("RGBA")
                image = self._trim_logo_alpha_content(image)

                # Resize the logo without stretching it out of proportion.
                target_w = min(300, image.width)
                ratio = target_w / image.width
                target_h = max(1, int(image.height * ratio))
                if image.width != target_w:
                    image = image.resize((target_w, target_h), Image.LANCZOS)

                # Slight sharpening helps the logo stay crisp after resizing.
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

    # Crop away transparent padding so the logo sits more neatly in the panel.
    def _trim_logo_alpha_content(self, image):
        alpha = image.split()[3]

        # Ignore tiny alpha noise at the edges and keep only real content.
        mask = alpha.point(lambda p: 255 if p > 8 else 0)
        bbox = mask.getbbox()
        if bbox:
            return image.crop(bbox)
        return image

    # Right side contains the sign-in card and form fields.
    def _build_right_panel(self, parent):
        self.right_backdrop = tk.Canvas(
            parent,
            bg=BG_MAIN,
            highlightthickness=0,
            bd=0,
        )
        self.right_backdrop.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.right_backdrop.bind("<Configure>", self._draw_right_backdrop)

        card_wrap = tk.Canvas(
            parent,
            bg=BG_MAIN,
            highlightthickness=0,
            bd=0,
            width=556,
            height=596,
        )
        card_wrap.place(relx=0.5, rely=0.5, anchor="center")
        card_wrap.bind("<Configure>", self._draw_signin_card)

        self.signin_content = tk.Frame(card_wrap, bg=BG_MAIN)
        card_wrap.create_window(278, 298, window=self.signin_content, width=420, height=482, anchor="center")

        content = self.signin_content

        # Page heading.
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

        # Password field gets its own wrapper because it includes the eye toggle.
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
            width=30,
            height=22,
            bg=FIELD_BG,
            highlightthickness=0,
            cursor=self.ui_cursor,
        )
        self.eye_btn.grid(row=0, column=1, padx=(0, 12))
        self._render_password_toggle_icon()

        self._set_password_placeholder()
        self._focus_ring(self.password_entry, self.password_wrap)

        self.password_entry.bind("<FocusIn>", self._password_focus_in)
        self.password_entry.bind("<FocusOut>", self._password_focus_out)

        self.eye_btn.bind("<Button-1>", lambda e: self._toggle_password())
        self.eye_btn.bind("<Enter>", lambda e: self._render_password_toggle_icon(color=METAL_LIGHT))
        self.eye_btn.bind("<Leave>", lambda e: self._render_password_toggle_icon())

        # Row under the fields for extra options.
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

        # Main login action button.
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

        # Password recovery link.
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

        # Small footer branding.
        tk.Label(
            content,
            text="PAMS  ·  Paragon Apartment Management Systems",
            bg=BG_MAIN,
            fg=TEXT_SUB,
            font=("Segoe UI", 7),
        ).pack(pady=(28, 0))

        # Start with the cursor in the username field.
        self.username_entry.focus_set()

        # Allow Enter to submit the form from either input box.
        self.username_entry.bind("<Return>", lambda e: self._login())
        self.password_entry.bind("<Return>", lambda e: self._login())

    # Draw layered rounded rectangles to create the sign-in card effect.
    def _draw_signin_card(self, event=None):
        canvas = event.widget if event else None
        if not canvas:
            return

        canvas.delete("card")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        self._create_rounded_rect(
            canvas,
            14,
            20,
            width - 6,
            height - 4,
            36,
            fill="#CDBCA6",
            outline="",
            tags="card",
        )
        self._create_rounded_rect(
            canvas,
            10,
            12,
            width - 12,
            height - 14,
            36,
            fill="#DCCFBD",
            outline="",
            tags="card",
        )
        self._create_rounded_rect(
            canvas,
            6,
            6,
            width - 16,
            height - 20,
            36,
            fill=BG_MAIN,
            outline="#D8CDBD",
            width=1,
            tags="card",
        )
        self._create_rounded_rect(
            canvas,
            7,
            7,
            width - 17,
            height - 21,
            35,
            fill="",
            outline="#ECE3D5",
            width=1,
            tags="card",
        )
        canvas.create_line(
            38,
            28,
            width - 52,
            28,
            fill=METAL,
            width=2,
            tags="card",
        )
        canvas.tag_lower("card")

    # Reusable helper for rounded card and button shapes drawn on a Canvas.
    def _create_rounded_rect(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    # Draw soft background shapes behind the sign-in card.
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
            outline="#E2D7C9",
            width=1,
        )
        canvas.create_oval(
            width * 0.45,
            height * 0.35,
            width * 1.25,
            height * 1.20,
            outline="#E9DECF",
            width=1,
        )
        canvas.create_line(
            width * 0.18,
            0,
            width * 0.18,
            height,
            fill="#E3D8CA",
            width=1,
        )

    # Create a standard input field with matching styling.
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

    # Swap border colours when the field gains or loses focus.
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

    # Clear placeholder text when the user starts typing.
    def _username_focus_in(self, event=None):
        if self.username_placeholder_active:
            self.username_entry.delete(0, tk.END)
            self.username_entry.config(fg=TEXT_ON_DARK)
            self.username_placeholder_active = False

    # Restore placeholder if the field is left empty.
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

    # Remove the fake placeholder and switch to password masking.
    def _password_focus_in(self, event=None):
        if self.password_placeholder_active:
            self.password_entry.delete(0, tk.END)
            self.password_entry.config(
                fg=TEXT_ON_DARK,
                show="" if self.show_password else "•"
            )
            self.password_placeholder_active = False

    # Put the placeholder back if the password box is empty.
    def _password_focus_out(self, event=None):
        if not self.password_entry.get():
            self._set_password_placeholder()

    # Switch between showing and hiding the password text.
    def _toggle_password(self):
        if self.password_placeholder_active:
            return

        self.show_password = not self.show_password

        if self.show_password:
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="•")
        self._render_password_toggle_icon()

    # Draw the password-eye icon, or use PNG icons if they were loaded successfully.
    def _render_password_toggle_icon(self, color=None):
        if self.using_image_eye_icons:
            state = "hide" if self.show_password else "show"
            shade = "hover" if color else "normal"
            icon_pack = self.eye_icon_hide if state == "hide" else self.eye_icon_show
            icon = icon_pack.get(shade) or icon_pack.get("normal")
            if icon:
                self.eye_btn.delete("all")
                cx = int(self.eye_btn.cget("width")) // 2
                cy = int(self.eye_btn.cget("height")) // 2
                self.eye_btn.create_image(cx, cy, image=icon, anchor="center")
                return

        stroke = color or TEXT_MUTED
        self.eye_btn.delete("all")
        cx = int(self.eye_btn.cget("width")) // 2
        cy = int(self.eye_btn.cget("height")) // 2

        # Basic eye shape drawn directly on the canvas.
        self.eye_btn.create_oval(cx - 10, cy - 5, cx + 10, cy + 5, outline=stroke, width=2)
        self.eye_btn.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, outline=stroke, fill=stroke, width=1)

        # Add a slash when the password is hidden.
        if not self.show_password:
            self.eye_btn.create_line(cx - 9, cy + 6, cx + 9, cy - 6, fill=stroke, width=2)

    # Load custom image icons for the password toggle if they exist.
    def _load_password_toggle_icons(self):
        if not PIL_AVAILABLE:
            return

        show_path = self._resolve_icon_path("show.png")
        hide_path = self._resolve_icon_path("hide.png")
        if not show_path or not hide_path:
            return

        show_normal = self._build_png_icon(show_path, brighten=1.0)
        show_hover = self._build_png_icon(show_path, brighten=1.22)
        hide_normal = self._build_png_icon(hide_path, brighten=1.0)
        hide_hover = self._build_png_icon(hide_path, brighten=1.22)

        if not all([show_normal, show_hover, hide_normal, hide_hover]):
            return

        self.eye_icon_show = {"normal": show_normal, "hover": show_hover}
        self.eye_icon_hide = {"normal": hide_normal, "hover": hide_hover}
        self.using_image_eye_icons = True

    # Check the common icon folders and return the first match found.
    def _resolve_icon_path(self, filename):
        candidates = [
            os.path.join("images", "icons", filename),
            os.path.join("images", filename),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    # Resize and optionally brighten icon images for normal and hover states.
    def _build_png_icon(self, image_path, brighten=1.0):
        try:
            image = Image.open(image_path).convert("RGBA").resize(self.eye_icon_size, Image.LANCZOS)
            if brighten != 1.0:
                image = ImageEnhance.Brightness(image).enhance(brighten)
            return ImageTk.PhotoImage(image)
        except Exception:
            return None

    # Restore the saved username if "remember me" was used previously.
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

    # Show help message instead of implementing self-service password reset.
    def _forgot_password(self, event=None):
        self._show_icon_modal(
            title="Forgot Password",
            message="Please contact your system\nadministrator to reset your\npassword.",
            icon_filename="forgotpassword.png",
            icon_attr_name="forgot_icon_image",
        )

    # Reusable popup for warnings and small system messages.
    def _show_icon_modal(self, title, message, icon_filename, icon_attr_name):
        modal = tk.Toplevel(self)
        modal.title(title)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.resizable(False, False)
        modal.configure(bg=BG_MAIN)

        width, height = 372, 298
        parent = self.winfo_toplevel()
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        modal.geometry(f"{width}x{height}+{x}+{y}")

        card = tk.Canvas(
            modal,
            bg=BG_MAIN,
            highlightthickness=0,
            bd=0,
        )
        card.pack(fill="both", expand=True, padx=8, pady=8)
        card.update_idletasks()
        self._create_rounded_rect(
            card,
            2,
            2,
            width - 20,
            height - 20,
            20,
            fill="#E7E6E2",
            outline="#C9C3B9",
            width=1,
        )

        content = tk.Frame(card, bg="#E7E6E2")
        card.create_window((width - 16) // 2, (height - 16) // 2, window=content, anchor="center")

        icon_label = tk.Label(content, bg="#E7E6E2")
        icon_label.pack(pady=(10, 4))

        icon_path = self._resolve_icon_path(icon_filename)
        if icon_path and PIL_AVAILABLE:
            try:
                image = Image.open(icon_path).convert("RGBA").resize((56, 56), Image.LANCZOS)
                setattr(self, icon_attr_name, ImageTk.PhotoImage(image))
                icon_label.configure(image=getattr(self, icon_attr_name), text="")
            except Exception:
                icon_label.configure(text="🔒", fg="#4B59D5", font=("Segoe UI Emoji", 28))
        else:
            icon_label.configure(text="🔒", fg="#4B59D5", font=("Segoe UI Emoji", 28))

        tk.Label(
            content,
            text=message,
            bg="#E7E6E2",
            fg="#3E4344",
            font=("Segoe UI", 11, "bold"),
            justify="center",
        ).pack(pady=(2, 10))

        button_canvas = tk.Canvas(
            content,
            width=228,
            height=42,
            bg="#E7E6E2",
            highlightthickness=0,
            bd=0,
            cursor=self.ui_cursor,
        )
        button_canvas.pack(pady=(0, 10))

        btn_normal = "#E650A1"
        btn_hover = "#DB3A8C"
        btn_text_color = "#FFFFFF"

        btn_shape = self._create_rounded_rect(
            button_canvas,
            2,
            2,
            226,
            40,
            12,
            fill=btn_normal,
            outline=btn_normal,
            width=1,
        )
        btn_text = button_canvas.create_text(
            114,
            21,
            text="OK",
            fill=btn_text_color,
            font=("Segoe UI", 12, "bold"),
        )

        def _btn_hover_in(event=None):
            button_canvas.itemconfig(btn_shape, fill=btn_hover, outline=btn_hover)

        def _btn_hover_out(event=None):
            button_canvas.itemconfig(btn_shape, fill=btn_normal, outline=btn_normal)

        def _btn_click(event=None):
            modal.destroy()

        for tag in (btn_shape, btn_text):
            button_canvas.tag_bind(tag, "<Enter>", _btn_hover_in)
            button_canvas.tag_bind(tag, "<Leave>", _btn_hover_out)
            button_canvas.tag_bind(tag, "<Button-1>", _btn_click)

        button_canvas.bind("<Enter>", _btn_hover_in)
        button_canvas.bind("<Leave>", _btn_hover_out)
        button_canvas.bind("<Button-1>", _btn_click)
        button_canvas.bind("<Return>", _btn_click)
        modal.bind("<Escape>", lambda e: modal.destroy())
        button_canvas.focus_set()

    # Validate input, try to log in, then handle success or failure.
    def _login(self):
        username = "" if self.username_placeholder_active else self.username_entry.get().strip()
        password = "" if self.password_placeholder_active else self.password_entry.get().strip()

        if not username or not password:
            self._show_icon_modal(
                title="Sign In Failed",
                message="Please enter your username\nand password.",
                icon_filename="signin.png",
                icon_attr_name="signin_icon_image",
            )
            return

        success, message = AuthController.login(username, password)

        if success:
            # Save or remove the remembered username depending on the checkbox state.
            if self.remember_var.get():
                with open("remember_me.txt", "w") as f:
                    f.write(username)
            elif os.path.exists("remember_me.txt"):
                os.remove("remember_me.txt")

            self.on_login_success(AuthController.get_current_role())
        else:
            self._show_icon_modal(
                title="Sign In Failed",
                message=message,
                icon_filename="signin.png",
                icon_attr_name="signin_icon_image",
            )