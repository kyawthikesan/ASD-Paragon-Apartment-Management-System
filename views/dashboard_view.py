import tkinter as tk
from views.tenant_view import TenantView
from views.apartment_view import ApartmentView
from views.lease_view import LeaseView


class DashboardView:

    def __init__(self, root):

        frame = tk.Frame(root)
        frame.pack(pady=100)

        tk.Label(frame, text="PAMS Dashboard", font=("Arial", 20)).pack(pady=20)

        tk.Button(frame, text="Tenant Management", width=25,
          command=lambda: self.open_tenant(root)).pack(pady=5)
        tk.Button(frame, text="Apartment Management", width=25,
          command=lambda: self.open_apartment(root)).pack(pady=5)
        tk.Button(frame, text="Lease Management", width=25,
          command=lambda: self.open_lease(root)).pack(pady=5)
        tk.Button(frame, text="Payments", width=25).pack(pady=5)
        tk.Button(frame, text="Maintenance", width=25).pack(pady=5)
        tk.Button(frame, text="Reports", width=25).pack(pady=5)
        
        
    def open_tenant(self, root):
        for widget in root.winfo_children():
            widget.destroy()

        TenantView(root)

    def open_apartment(self, root):
        for widget in root.winfo_children():
            widget.destroy()

        ApartmentView(root)

    def open_lease(self, root):
        for widget in root.winfo_children():
            widget.destroy()

        LeaseView(root)