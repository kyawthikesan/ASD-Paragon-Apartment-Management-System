import tkinter as tk
from tkinter import messagebox
from controllers.tenant_controller import TenantController
from tkinter import messagebox, ttk

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
        self.ni.bind("<KeyRelease>", self.uppercase_ni)

        tk.Label(frame, text="Phone").grid(row=3, column=0)
        vcmd = (root.register(self.validate_phone), "%P")

        self.phone = tk.Entry(frame, validate="key", validatecommand=vcmd)
        self.phone.grid(row=3, column=1)

        tk.Label(frame, text="Email").grid(row=4, column=0)
        self.email = tk.Entry(frame)
        self.email.grid(row=4, column=1)

        tk.Button(frame, text="Add Tenant", command=self.add_tenant).grid(row=5, columnspan=2, pady=10)
        tk.Button(frame, text="Update Tenant", command=self.update_tenant).grid(row=6, column=2)
        tk.Button(frame, text="Delete Tenant", command=self.delete_tenant).grid(row=7, columnspan=2)


        columns = ("ID", "Name", "NI Number", "Phone", "Email")

        self.table = ttk.Treeview(root, columns=columns, show="headings")

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=120)

        self.table.pack(pady=20)

        self.table.bind("<<TreeviewSelect>>", self.fill_fields)                           

        self.load_tenants()

    def load_tenants(self):

        for row in self.table.get_children():
            self.table.delete(row)

        tenants = TenantController.get_all_tenants()

        for tenant in tenants:
            self.table.insert("", tk.END, values=tenant)

    def fill_fields(self, event):

        selected = self.table.selection()

        if not selected:
            return

        values = self.table.item(selected[0], "values")

        self.name.delete(0, tk.END)
        self.name.insert(0, values[1])

        self.ni.delete(0, tk.END)
        self.ni.insert(0, values[2])

        self.phone.delete(0, tk.END)
        self.phone.insert(0, values[3])

        self.email.delete(0, tk.END)
        self.email.insert(0, values[4])



    def validate_phone(self, P):
        return P.isdigit() or P == ""

    def uppercase_ni(self, event):
        current = self.ni.get()
        self.ni.delete(0, tk.END)
        self.ni.insert(0, current.upper())
        self.ni.icursor(tk.END) 

    def add_tenant(self):

        name = self.name.get()
        ni = self.ni.get()
        phone = self.phone.get()
        email = self.email.get()

        if not name or not ni or not phone:
            messagebox.showerror("Error", "Name, NI and Phone are required")
            return

        TenantController.add_tenant(name, ni, phone, email)
        messagebox.showinfo("Success", "Tenant Added")

        self.load_tenants()

        # clear fields
        self.name.delete(0, tk.END)
        self.ni.delete(0, tk.END)
        self.phone.delete(0, tk.END)
        self.email.delete(0, tk.END)

    


    def go_back(self, root):

        from views.dashboard_view import DashboardView

        for widget in root.winfo_children():
            widget.destroy()

        DashboardView(root)

    def delete_tenant(self):

        selected = self.table.selection()

        if not selected:
            messagebox.showerror("Error", "Please select a tenant")
            return

        values = self.table.item(selected[0], "values")
        tenant_id = values[0]

        TenantController.delete_tenant(tenant_id)

        messagebox.showinfo("Success", "Tenant deleted")

        self.load_tenants()

    def update_tenant(self):

        selected = self.table.selection()

        if not selected:
            messagebox.showerror("Error", "Please select a tenant")
            return

        values = self.table.item(selected[0], "values")
        tenant_id = values[0]

        name = self.name.get()
        ni = self.ni.get()
        phone = self.phone.get()
        email = self.email.get()

        TenantController.update_tenant(tenant_id, name, ni, phone, email)

        messagebox.showinfo("Success", "Tenant updated")

        self.load_tenants()

        # clear fields
        self.name.delete(0, tk.END)
        self.ni.delete(0, tk.END)
        self.phone.delete(0, tk.END)
        self.email.delete(0, tk.END)

    