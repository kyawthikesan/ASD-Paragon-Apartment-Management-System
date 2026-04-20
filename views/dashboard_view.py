import tkinter as tk
from tkinter import ttk
from controllers.auth_controller import AuthController


class DashboardView(ttk.Frame):
    def __init__(self, parent, on_logout, open_user_management,
             open_tenant_management, open_apartment_management, open_lease_management):
        super().__init__(parent, padding=20)
        self.grid(sticky="nsew")

        current_user = AuthController.current_user
        role = current_user["role_name"]

        ttk.Label(
            self,
            text=f"PAMS Dashboard - {role.replace('_', ' ').title()}",
            font=("Arial", 16, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))

        ttk.Label(
            self,
            text=f"Logged in as: {current_user['full_name']}"
        ).grid(row=1, column=0, sticky="w", pady=5)

        row_num = 2

        if role == "admin":
            ttk.Button(
                self,
                text="Manage Users",
                command=open_user_management
            ).grid(row=row_num, column=0, sticky="w", pady=5)
            row_num += 1

        #Member_2
        ttk.Button(
            self,
            text="Tenant Management",
            command=open_tenant_management
        ).grid(row=row_num, column=0, sticky="w", pady=5)
        row_num += 1

        ttk.Button(
            self,
            text="Apartment Management",
            command=open_apartment_management
        ).grid(row=row_num, column=0, sticky="w", pady=5)
        row_num += 1

        ttk.Button(
            self,
            text="Lease Management",
            command=open_lease_management
        ).grid(row=row_num, column=0, sticky="w", pady=5)
        row_num += 1

        ttk.Button(
            self,
            text="Logout",
            command=on_logout
        ).grid(row=row_num, column=0, sticky="w", pady=15)