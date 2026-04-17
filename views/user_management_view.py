import tkinter as tk
from tkinter import ttk, messagebox
from dao.user_dao import UserDAO


class UserManagementView(ttk.Frame):
    def __init__(self, parent, go_back):
        super().__init__(parent, padding=20)
        self.go_back = go_back
        self.grid(sticky="nsew")

        ttk.Label(self, text="User Management", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 15)
        )

        ttk.Label(self, text="Full Name").grid(row=1, column=0, sticky="w")
        self.full_name_entry = ttk.Entry(self, width=30)
        self.full_name_entry.grid(row=1, column=1, pady=5)

        ttk.Label(self, text="Username").grid(row=2, column=0, sticky="w")
        self.username_entry = ttk.Entry(self, width=30)
        self.username_entry.grid(row=2, column=1, pady=5)

        ttk.Label(self, text="Password").grid(row=3, column=0, sticky="w")
        self.password_entry = ttk.Entry(self, width=30, show="*")
        self.password_entry.grid(row=3, column=1, pady=5)

        ttk.Label(self, text="Role").grid(row=4, column=0, sticky="w")
        self.role_combo = ttk.Combobox(
            self,
            values=["admin", "front_desk", "finance", "maintenance", "manager"],
            state="readonly",
            width=27
        )
        self.role_combo.grid(row=4, column=1, pady=5)
        self.role_combo.current(0)

        ttk.Label(self, text="Location").grid(row=5, column=0, sticky="w")
        self.location_entry = ttk.Entry(self, width=30)
        self.location_entry.grid(row=5, column=1, pady=5)

        ttk.Button(self, text="Create User", command=self.create_user).grid(
            row=6, column=0, columnspan=2, pady=10
        )

        self.tree = ttk.Treeview(
            self,
            columns=("ID", "Name", "Username", "Role", "Location", "Active"),
            show="headings",
            height=8
        )
        for col in ("ID", "Name", "Username", "Role", "Location", "Active"):
            self.tree.heading(col, text=col)
        self.tree.grid(row=7, column=0, columnspan=2, pady=10)

        ttk.Button(self, text="Deactivate Selected", command=self.deactivate_selected).grid(
            row=8, column=0, sticky="w", pady=5
        )

        ttk.Button(self, text="Back", command=self.go_back).grid(
            row=8, column=1, sticky="e", pady=5
        )

        self.load_users()

    def create_user(self):
        try:
            UserDAO.create_user(
                self.full_name_entry.get().strip(),
                self.username_entry.get().strip(),
                self.password_entry.get().strip(),
                self.role_combo.get(),
                self.location_entry.get().strip() or None
            )
            messagebox.showinfo("Success", "User created successfully.")
            self.load_users()
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for user in UserDAO.get_all_users():
            self.tree.insert("", "end", values=(
                user["id"],
                user["full_name"],
                user["username"],
                user["role_name"],
                user["location"],
                "Yes" if user["is_active"] == 1 else "No"
            ))

    def deactivate_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a user first.")
            return

        user_id = self.tree.item(selected[0])["values"][0]
        UserDAO.deactivate_user(user_id)
        self.load_users()
        messagebox.showinfo("Success", "User deactivated.")