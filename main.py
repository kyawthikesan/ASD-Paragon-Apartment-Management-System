import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import traceback
import sys
import os

from database.db_manager import DBManager
from dao.user_dao import UserDAO
from dao.lease_dao import LeaseDAO

from controllers.auth_controller import AuthController

from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.user_management_view import UserManagementView
from views.tenant_view import TenantView
from views.apartment_view import ApartmentView
from views.lease_view import LeaseView
from views.payment_view import FinanceDashboardView
from views.maintenance_view import MaintenanceDashboardView

from styles.ttk_theme import apply_ttk_theme
from styles.colors import LEFT_BG, BG_MAIN


class PAMSApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Paragon Apartment Management System")
        self.configure(bg=LEFT_BG)
        apply_ttk_theme(self)

        # Start size before maximizing
        self.center_window(1100, 700)

        # Better desktop minimum size
        self.minsize(900, 580)

        # Maximize safely across platforms
        self._maximize_window()

        # Root expands fully
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main container: every view is placed here
        self.container = tk.Frame(self, bg=LEFT_BG, highlightthickness=0, bd=0)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Window icon
        try:
            self.iconbitmap("images/logo.ico")
        except Exception:
            try:
                from PIL import Image, ImageTk
                icon = Image.open("images/logo.png").resize((32, 32))
                self._icon = ImageTk.PhotoImage(icon)
                self.iconphoto(True, self._icon)
            except Exception:
                pass

        self.current_view = None

        # Database setup
        if not os.path.exists("pams.db"):
            DBManager.initialise_database()
            DBManager.run_seed()
        else:
            DBManager.initialise_database()

        UserDAO.seed_roles()
        self.ensure_default_admin()

        self.show_login()

    def center_window(self, width, height):
        """Center the window on screen before maximizing."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

    def _maximize_window(self):
        """
        Maximize safely.
        macOS sometimes crashes with zoom-style maximize calls,
        so use a safer geometry-based fallback there.
        """
        if sys.platform == "darwin":
            self.update_idletasks()
            width = self.winfo_screenwidth()
            height = self.winfo_screenheight()
            safe_height = max(700, height - 72)
            self.geometry(f"{width}x{safe_height}+0+25")
            return

        try:
            self.state("zoomed")
            return
        except tk.TclError:
            pass

        try:
            self.attributes("-zoomed", True)
            return
        except tk.TclError:
            pass

        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()
        self.geometry(f"{width}x{height}+0+0")

    def clear_view(self):
        """Destroy all widgets inside the main container."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        """Show login screen."""
        self.configure(bg=BG_MAIN)
        self.container.configure(bg=BG_MAIN)
        self.clear_view()

        # LoginView usually expects parent container + success callback
        self.current_view = LoginView(self.container, self.route_dashboard_by_role)

    def route_dashboard_by_role(self, role: str | None = None):
        """Route user to the correct dashboard based on role."""
        role_name = role or AuthController.get_current_role()

        if role_name == "admin":
            self.show_admin_dashboard()
        elif role_name == "front_desk":
            self.show_front_desk_dashboard()
        elif role_name == "finance":
            self.show_finance_dashboard()
        elif role_name == "maintenance":
            self.show_maintenance_dashboard()
        elif role_name == "manager":
            self.show_manager_dashboard()
        else:
            self.logout()

    def show_dashboard(self):
        """Show main dashboard for admin / manager / front desk."""
        self.configure(bg=LEFT_BG)
        self.container.configure(bg=LEFT_BG)
        self.clear_view()

        try:
            # Try the newer signature first (includes finance callback)
            try:
                self.current_view = DashboardView(
                    self.container,
                    self.logout,
                    self.show_user_management,
                    self.show_tenant_management,
                    self.show_apartment_management,
                    self.show_lease_management,
                    self.show_finance_dashboard,
                    self.show_finance_payments,
                    self.show_finance_reports,
                )
            except TypeError:
                # Fallback to older signature if DashboardView only accepts 6 callbacks
                self.current_view = DashboardView(
                    self.container,
                    self.logout,
                    self.show_user_management,
                    self.show_tenant_management,
                    self.show_apartment_management,
                    self.show_lease_management
                )

        except Exception as error:
            details = traceback.format_exc(limit=8)

            fallback = ttk.Frame(self.container, padding=24)
            fallback.pack(fill="both", expand=True)

            ttk.Label(
                fallback,
                text="Dashboard failed to load",
                font=("Arial", 14, "bold")
            ).pack(anchor="w", pady=(0, 8))

            ttk.Label(
                fallback,
                text=str(error)
            ).pack(anchor="w", pady=(0, 8))

            ttk.Label(
                fallback,
                text=details
            ).pack(anchor="w")

            ttk.Button(
                fallback,
                text="Back to Login",
                command=self.logout
            ).pack(anchor="w", pady=(12, 0))

            self.current_view = fallback

    def show_admin_dashboard(self):
        self.show_dashboard()

    def show_manager_dashboard(self):
        self.show_dashboard()

    def show_front_desk_dashboard(self):
        self.show_dashboard()

    def show_finance_dashboard(self, initial_tab="Invoices", visible_tabs=None):
        """Open finance dashboard with selected starting tab."""
        self._show_role_view(
            FinanceDashboardView,
            "Finance Dashboard",
            initial_tab=initial_tab,
            visible_tabs=visible_tabs,
        )

    def show_finance_payments(self):
        self.show_finance_dashboard("Payments", visible_tabs=("Invoices", "Payments"))

    def show_finance_reports(self):
        self.show_finance_dashboard("Reports", visible_tabs=("Reports",))

    def show_maintenance_dashboard(self):
        self._show_role_view(MaintenanceDashboardView, "Maintenance Dashboard")

    def _show_role_view(self, view_class, view_name: str, **view_kwargs):
        """
        Open role-specific dashboard.
        Tries multiple constructor styles to support your different screen classes.
        """
        self.configure(bg=LEFT_BG)
        self.container.configure(bg=LEFT_BG)
        self.clear_view()

        try:
            try:
                # Newer / more complete constructor style
                self.current_view = view_class(
                    self.container,
                    self.logout,
                    self.route_dashboard_by_role,
                    **view_kwargs
                )
            except TypeError:
                try:
                    # Simpler container-based constructor
                    self.current_view = view_class(
                        self.container,
                        self.logout,
                        **view_kwargs
                    )
                except TypeError:
                    # Older root-based constructor
                    self.current_view = view_class(
                        self,
                        self.logout,
                        self.route_dashboard_by_role,
                        **view_kwargs
                    )

        except Exception as error:
            details = traceback.format_exc(limit=8)

            fallback = ttk.Frame(self.container, padding=24)
            fallback.pack(fill="both", expand=True)

            ttk.Label(
                fallback,
                text=f"{view_name} failed to load",
                font=("Arial", 14, "bold")
            ).pack(anchor="w", pady=(0, 8))

            ttk.Label(
                fallback,
                text=str(error)
            ).pack(anchor="w", pady=(0, 8))

            ttk.Label(
                fallback,
                text=details
            ).pack(anchor="w")

            ttk.Button(
                fallback,
                text="Back to Login",
                command=self.logout
            ).pack(anchor="w", pady=(12, 0))

            self.current_view = fallback

    def _require_feature_access(self, feature_key: str, feature_name: str) -> bool:
        """Check whether current role can access a feature."""
        role = AuthController.get_current_role()
        if AuthController.can_access_feature(feature_key, role):
            return True

        self._show_access_denied_modal(feature_name)
        return False

    def _show_access_denied_modal(self, feature_name: str):
        """Show animated access denied popup."""
        root = self

        # Get current window position + size
        root.update_idletasks()
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()

        # Modal size
        width = 620
        height = 460

        # Centered final position
        final_x = x + (w // 2) - (width // 2)
        final_y = y + (h // 2) - (height // 2)

        # Start slightly lower for slide-up animation
        start_y = final_y + 18

        modal = tk.Toplevel(root)
        modal.overrideredirect(True)
        modal.configure(bg="#000000")
        modal.geometry(f"{width}x{height}+{final_x}+{start_y}")

        # Start transparent
        try:
            modal.attributes("-alpha", 0.0)
        except Exception:
            pass

        def finish_and_refresh():
            """Destroy modal and refresh dashboard after close."""
            try:
                modal.destroy()
            except Exception:
                pass
            self.route_dashboard_by_role()

        def fade_out(alpha=1.0, current_y=None):
            """Fade-out + slight downward motion."""
            if current_y is None:
                current_y = modal.winfo_y()

            alpha -= 0.10
            current_y += 2

            if alpha <= 0:
                finish_and_refresh()
                return

            try:
                modal.attributes("-alpha", alpha)
            except Exception:
                pass

            modal.geometry(f"{width}x{height}+{final_x}+{current_y}")
            modal.after(16, lambda: fade_out(alpha, current_y))

        def close_modal():
            fade_out()

        # Shadow layer
        shadow = ctk.CTkFrame(
            modal,
            fg_color="#000000",
            corner_radius=28
        )
        shadow.pack(fill="both", expand=True)

        # Main popup card
        card = ctk.CTkFrame(
            shadow,
            fg_color="#F7F7FA",
            corner_radius=28
        )
        card.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.965,
            relheight=0.965
        )

        ctk.CTkFrame(card, fg_color="transparent", height=20).pack()

        # Circular icon background
        icon_circle = ctk.CTkFrame(
            card,
            width=110,
            height=110,
            corner_radius=55,
            fg_color="#F6EEF3"
        )
        icon_circle.pack(pady=(10, 10))
        icon_circle.pack_propagate(False)

        # Load custom icon if found
        try:
            from PIL import Image, ImageTk
            icon_path = os.path.join("images", "icons", "access_denied.png")

            if os.path.exists(icon_path):
                img = Image.open(icon_path).convert("RGBA").resize((50, 50))
                icon_img = ImageTk.PhotoImage(img)

                label = tk.Label(
                    icon_circle,
                    image=icon_img,
                    bg="#F6EEF3",
                    bd=0,
                    highlightthickness=0
                )
                label.image = icon_img
                label.pack(expand=True)
            else:
                raise FileNotFoundError
        except Exception:
            # Fallback emoji icon
            tk.Label(
                icon_circle,
                text="🔒",
                bg="#F6EEF3",
                fg="#E94B93",
                font=("Arial", 26),
                bd=0
            ).pack(expand=True)

        ctk.CTkLabel(
            card,
            text=f"{feature_name} is not\navailable for your role.",
            text_color="#24314F",
            font=("Arial", 22, "bold"),
            justify="center"
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            card,
            text="You don't have permission to access this section.\n"
                 "Please contact your administrator for more information.",
            text_color="#6E7893",
            font=("Arial", 13),
            justify="center"
        ).pack(pady=(0, 20))

        ctk.CTkButton(
            card,
            text="OK",
            command=close_modal,
            fg_color="#F34F98",
            hover_color="#E2448B",
            text_color="#FFFFFF",
            corner_radius=22,
            font=("Arial", 18, "bold"),
            height=50,
            width=260
        ).pack(pady=(10, 20))

        modal.bind("<Escape>", lambda e: close_modal())
        modal.lift()
        modal.focus_force()

        def fade_in(alpha=0.0, current_y=None):
            """Fade-in + slight upward motion."""
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

        fade_in()

    def show_user_management(self):
        if not self._require_feature_access("user_management", "User Management"):
            return

        self.clear_view()
        self.current_view = UserManagementView(self.container, self.show_dashboard)

    def show_tenant_management(self):
        if not self._require_feature_access("tenant_management", "Tenant Management"):
            return

        self.clear_view()
        self.current_view = TenantView(self.container, self.show_dashboard)

    def show_apartment_management(self):
        if not self._require_feature_access("apartment_management", "Apartment Management"):
            return

        self.clear_view()
        self.current_view = ApartmentView(self.container, self.show_dashboard)

    def show_lease_management(self):
        if not self._require_feature_access("lease_management", "Lease Management"):
            return

        self.clear_view()
        LeaseDAO.expire_leases()
        self.current_view = LeaseView(self.container, self.show_dashboard)

    def logout(self):
        AuthController.logout()
        self.show_login()

    def ensure_default_admin(self):
        """Create default admin if it doesn't exist."""
        try:
            if UserDAO.get_user_by_username("admin") is None:
                UserDAO.create_user(
                    full_name="System Administrator",
                    username="admin",
                    password="admin123",
                    role_name="admin",
                    location="Bristol"
                )
        except Exception as e:
            print("Error creating default admin:", e)


if __name__ == "__main__":
    app = PAMSApp()
    app.mainloop()
