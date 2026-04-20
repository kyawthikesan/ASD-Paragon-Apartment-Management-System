import tkinter as tk
from tkinter import ttk
from database.db_manager import DBManager
from dao.user_dao import UserDAO
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.user_management_view import UserManagementView
from controllers.auth_controller import AuthController
from views.tenant_view import TenantView
from views.apartment_view import ApartmentView
from views.lease_view import LeaseView
from dao.lease_dao import LeaseDAO
import os

class PAMSApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Paragon Apartment Management System")
        self.configure(bg="#1C1A17")          # deep black-brown to match login view
        self.center_window(1100, 700)
        self.minsize(950, 600)

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

        if not os.path.exists("pams.db"):
            DBManager.initialise_database()
            DBManager.run_seed()
        else:
            DBManager.initialise_database()

        UserDAO.seed_roles()
        self.ensure_default_admin()

        self.show_login()

    def center_window(self, width, height):
        self.update_idletasks()
        screen_width  = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width  // 2) - (width  // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def clear_view(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        self.configure(bg="#1C1A17")          # dark canvas for login
        self.clear_view()
        self.current_view = LoginView(self, self.route_dashboard_by_role)

    def route_dashboard_by_role(self, role: str | None = None):
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
        self.configure(bg="#1C1A17")          # dashboard sets its own bg
        self.clear_view()
        self.current_view = DashboardView(
            self,
            self.logout,
            self.show_user_management,
            self.show_tenant_management,
            self.show_apartment_management,
            self.show_lease_management
        )

    def show_admin_dashboard(self):
        self.show_dashboard()

    def show_manager_dashboard(self):
        self.show_dashboard()

    def show_front_desk_dashboard(self):
        self.show_dashboard()

    def show_finance_dashboard(self):
        self._show_role_placeholder("Finance Manager")

    def show_maintenance_dashboard(self):
        self._show_role_placeholder("Maintenance Staff")

    def _show_role_placeholder(self, role_title: str):
        self.configure(bg="#1C1A17")
        self.clear_view()

        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=f"{role_title} Dashboard",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            frame,
            text="This role dashboard is connected and ready for feature modules."
        ).pack(anchor="w", pady=(0, 16))

        ttk.Button(frame, text="Logout", command=self.logout).pack(anchor="w")
        self.current_view = frame

    def show_user_management(self):
        self.clear_view()
        self.current_view = UserManagementView(self, self.show_dashboard)

    def show_tenant_management(self):
        self.clear_view()
        self.current_view = TenantView(self, self.show_dashboard)


    def show_apartment_management(self):
        self.clear_view()
        self.current_view = ApartmentView(self, self.show_dashboard)


    def show_lease_management(self):
        self.clear_view()
        LeaseDAO.expire_leases()
        self.current_view = LeaseView(self, self.show_dashboard)

    def logout(self):
        AuthController.logout()
        self.show_login()

    def ensure_default_admin(self):
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
