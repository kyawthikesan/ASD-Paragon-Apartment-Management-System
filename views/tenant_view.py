import tkinter as tk
from tkinter import messagebox
from controllers.tenant_controller import TenantController


class TenantView:

    def __init__(self, root):

        self.root = root

        frame = tk.Frame(root)
        frame.pack(pady=20)

        tk.Button(root, text="Back", command=lambda: self.go_back(root)).pack()

        tk.Label(frame, text="Tenant Management", font=("Arial", 18)).grid(row=0, columnspan=2, pady=10)

        tk.Label(frame, text="Name").grid(row=1, column=0)
        self.name = tk.Entry(frame)
        self.name.grid(row=1, column=1)

        tk.Label(frame, text="NI Number").grid(row=2, column=0)
        self.ni = tk.Entry(frame)
        self.ni.grid(row=2, column=1)

        tk.Label(frame, text="Phone").grid(row=3, column=0)
        self.phone = tk.Entry(frame)
        self.phone.grid(row=3, column=1)

        tk.Label(frame, text="Email").grid(row=4, column=0)
        self.email = tk.Entry(frame)
        self.email.grid(row=4, column=1)

        tk.Button(frame, text="Add Tenant", command=self.add_tenant).grid(row=5, columnspan=2, pady=10)

        self.listbox = tk.Listbox(root, width=70)
        self.listbox.pack(pady=20)

        self.load_tenants()

    def add_tenant(self):

        name = self.name.get()
        ni = self.ni.get()
        phone = self.phone.get()
        email = self.email.get()

        TenantController.add_tenant(name, ni, phone, email)

        messagebox.showinfo("Success", "Tenant Added")

        self.load_tenants()

    def load_tenants(self):

        self.listbox.delete(0, tk.END)

        tenants = TenantController.get_all_tenants()

        for t in tenants:
            self.listbox.insert(tk.END, f"ID:{t[0]} | {t[1]} | {t[2]} | {t[3]} | {t[4]}")

    def go_back(self, root):

        from views.dashboard_view import DashboardView

        for widget in root.winfo_children():
            widget.destroy()

        DashboardView(root)