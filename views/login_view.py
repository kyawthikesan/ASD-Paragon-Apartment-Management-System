import tkinter as tk
from tkinter import messagebox
from controllers.login_controller import LoginController


class LoginView:
    def __init__(self, root):
        self.root = root

        self.frame = tk.Frame(root)
        self.frame.pack(pady=150)

        tk.Label(self.frame, text="Login to PAMS", font=("Arial", 16)).grid(row=0, columnspan=2, pady=10)

        tk.Label(self.frame, text="Username").grid(row=1, column=0, sticky="e", padx=5)
        self.username_entry = tk.Entry(self.frame)
        self.username_entry.grid(row=1, column=1, padx=5)

        tk.Label(self.frame, text="Password").grid(row=2, column=0, sticky="e", padx=5)
        self.password_entry = tk.Entry(self.frame, show="*")
        self.password_entry.grid(row=2, column=1, padx=5)

        tk.Button(self.frame, text="Login", command=self.login).grid(row=3, columnspan=2, pady=10)

        self.root.bind("<Return>", lambda _event: self.login())

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password.")
            return

        user = LoginController.authenticate(username, password)

        if user:
            role = user["role"]

            for widget in self.root.winfo_children():
                widget.destroy()

            from views.dashboard_view import DashboardView
            DashboardView(self.root, role)
        else:
            messagebox.showerror("Error", "Invalid login")