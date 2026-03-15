import tkinter as tk
from tkinter import messagebox
from controllers.lease_controller import LeaseController


class LeaseView:

    def __init__(self, root):

        frame = tk.Frame(root)
        frame.pack(pady=20)

        tk.Button(root, text="Back", command=lambda: self.go_back(root)).pack()

        tk.Label(frame, text="Assign Apartment to Tenant", font=("Arial", 18)).grid(row=0, columnspan=2)

        tk.Label(frame, text="Tenant ID").grid(row=1, column=0)
        self.tenant = tk.Entry(frame)
        self.tenant.grid(row=1, column=1)

        tk.Label(frame, text="Apartment ID").grid(row=2, column=0)
        self.apartment = tk.Entry(frame)
        self.apartment.grid(row=2, column=1)

        tk.Label(frame, text="Start Date").grid(row=3, column=0)
        self.start = tk.Entry(frame)
        self.start.grid(row=3, column=1)

        tk.Label(frame, text="End Date").grid(row=4, column=0)
        self.end = tk.Entry(frame)
        self.end.grid(row=4, column=1)

        tk.Button(frame, text="Create Lease", command=self.create_lease).grid(row=5, columnspan=2, pady=10)

        self.listbox = tk.Listbox(root, width=80)
        self.listbox.pack(pady=20)

        self.load_leases()

    def create_lease(self):

        tenant = self.tenant.get()
        apartment = self.apartment.get()
        start = self.start.get()
        end = self.end.get()

        LeaseController.create_lease(tenant, apartment, start, end)

        messagebox.showinfo("Success", "Lease Created")

        self.load_leases()

    def load_leases(self):

        self.listbox.delete(0, tk.END)

        leases = LeaseController.get_leases()

        for lease in leases:
            self.listbox.insert(tk.END, lease)

    def go_back(self, root):
        
        from views.dashboard_view import DashboardView

        for widget in root.winfo_children():
            widget.destroy()

        DashboardView(root)