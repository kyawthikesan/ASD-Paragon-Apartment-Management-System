import tkinter as tk
from tkinter import ttk, messagebox
from dao.user_dao import UserDAO


class UserManagementView(ttk.Frame):
    def __init__(self, parent, go_back):
        super().__init__(parent, padding=20)
        self.go_back = go_back
        self.selected_user_id = None
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
        ttk.Label(self, text="(leave blank to keep current password)").grid(
            row=3, column=2, sticky="w", padx=(8, 0)
        )

        ttk.Label(self, text="Role").grid(row=4, column=0, sticky="w")
        self.role_values = UserDAO.get_roles()
        self.role_combo = ttk.Combobox(
            self,
            values=self.role_values,
            state="readonly",
            width=27
        )
        self.role_combo.grid(row=4, column=1, pady=5)
        if self.role_values:
            self.role_combo.current(0)

        ttk.Label(self, text="Location").grid(row=5, column=0, sticky="w")
        self.location_entry = ttk.Entry(self, width=30)
        self.location_entry.grid(row=5, column=1, pady=5)

        self.active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self,
            text="Active account",
            variable=self.active_var
        ).grid(row=6, column=1, sticky="w", pady=(2, 6))

        ttk.Button(self, text="Create User", command=self.create_user).grid(row=7, column=0, pady=10, sticky="w")
        ttk.Button(self, text="Update Selected", command=self.update_selected_user).grid(
            row=7, column=1, pady=10, sticky="e"
        )

        self.tree = ttk.Treeview(
            self,
            columns=("ID", "Name", "Username", "Role", "Location", "Active"),
            show="headings",
            height=8
        )
        for col in ("ID", "Name", "Username", "Role", "Location", "Active"):
            self.tree.heading(col, text=col)
        self.tree.grid(row=8, column=0, columnspan=2, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_user_select)

        ttk.Button(self, text="Deactivate Selected", command=self.deactivate_selected).grid(
            row=9, column=0, sticky="w", pady=5
        )

        ttk.Button(self, text="Back", command=self.go_back).grid(
            row=9, column=1, sticky="e", pady=5
        )

        self.load_users()

    def create_user(self):
        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role_name = self.role_combo.get().strip()
        location = self.location_entry.get().strip() or None
        is_active = 1 if self.active_var.get() else 0

        if not full_name or not username or not password or not role_name:
            messagebox.showerror("Error", "Full name, username, password, and role are required.")
            return

        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters.")
            return

        try:
            UserDAO.create_user(
                full_name,
                username,
                password,
                role_name,
                location,
                is_active
            )
            messagebox.showinfo("Success", "User created successfully.")
            self._reset_form()
            self.load_users()
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def _reset_form(self):
        self.full_name_entry.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.location_entry.delete(0, tk.END)
        self.active_var.set(True)
        self.selected_user_id = None
        if self.role_values:
            self.role_combo.current(0)

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

    def on_user_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0])["values"]
        self.selected_user_id = values[0]

        self.full_name_entry.delete(0, tk.END)
        self.full_name_entry.insert(0, values[1])

        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, values[2])

        role_name = values[3]
        if role_name in self.role_values:
            self.role_combo.set(role_name)

        self.location_entry.delete(0, tk.END)
        if values[4]:
            self.location_entry.insert(0, values[4])

        self.active_var.set(values[5] == "Yes")
        self.password_entry.delete(0, tk.END)

    def update_selected_user(self):
        if self.selected_user_id is None:
            messagebox.showwarning("Warning", "Select a user from the table first.")
            return

        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role_name = self.role_combo.get().strip()
        location = self.location_entry.get().strip() or None
        is_active = 1 if self.active_var.get() else 0

        if not full_name or not username or not role_name:
            messagebox.showerror("Error", "Full name, username, and role are required.")
            return

        if password and len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters.")
            return

        try:
            UserDAO.update_user(
                self.selected_user_id,
                full_name,
                username,
                role_name,
                location,
                is_active,
                password or None
            )
            messagebox.showinfo("Success", "User updated successfully.")
            self._reset_form()
            self.load_users()
        except Exception as error:
            messagebox.showerror("Error", str(error))
