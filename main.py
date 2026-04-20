import tkinter as tk
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

from database.db_manager import DBManager



class PAMSApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Paragon Apartment Management System")
        self.configure(bg="#1C1A17")          # deep black-brown — matches LoginView canvas
        self.center_window(1100, 700)
        self.minsize(950, 600)

        # Window icon (optional — place logo.ico or logo.png in images/)
        try:
            self.iconbitmap("images/logo.ico")
        except Exception:
            try:
                from PIL import Image, ImageTk
                icon = Image.open("images/logo.png").resize((32, 32))
                self._icon = ImageTk.PhotoImage(icon)
                self.iconphoto(True, self._icon)
            except Exception:
                pass                          # no icon — silently skip

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
        self.current_view = LoginView(self, self.show_dashboard)

    def show_dashboard(self):
        self.configure(bg="#1C1A17")          # keep consistent; dashboard sets its own bg
        self.clear_view()
        self.current_view = DashboardView(
            self,
            self.logout,
            self.show_user_management,
            self.show_tenant_management,
            self.show_apartment_management,
            self.show_lease_management
        )

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