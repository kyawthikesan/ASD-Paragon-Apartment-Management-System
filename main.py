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


class PAMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Paragon Apartment Management System")
        self.geometry("800x500")
        self.configure(bg="#f5f1eb")

        DBManager.initialise_database()
        UserDAO.seed_roles()
        self.ensure_default_admin()

        self.current_view = None
        self.show_login()

    def clear_view(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_view()

        container = tk.Frame(self, bg="#f5f1eb")
        container.pack(expand=True, fill="both")

        self.current_view = LoginView(container, self.show_dashboard)

    def show_dashboard(self):
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
        self.current_view = LeaseView(self, self.show_dashboard)

    def logout(self):
        AuthController.logout()
        self.show_login()

    def ensure_default_admin(self):
        if UserDAO.get_user_by_username("admin") is None:
            UserDAO.create_user(
                full_name="System Administrator",
                username="admin",
                password="admin123",
                role_name="admin",
                location="Bristol"
            )


if __name__ == "__main__":
    app = PAMSApp()
    app.mainloop()