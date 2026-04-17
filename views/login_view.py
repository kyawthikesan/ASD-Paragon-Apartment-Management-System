import tkinter as tk
from tkinter import ttk, messagebox
from controllers.auth_controller import AuthController


class LoginView(ttk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, padding=30, style="Card.TFrame")
        self.on_login_success = on_login_success

        self.setup_styles()

        self.pack(expand=True)  

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="PAMS Login", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )

        ttk.Label(self, text="Username", style="Custom.TLabel").grid(
            row=1, column=0, sticky="w", pady=8, padx=(0, 10)
        )
        self.username_entry = ttk.Entry(self, width=28)
        self.username_entry.grid(row=1, column=1, pady=8, sticky="ew")

        ttk.Label(self, text="Password", style="Custom.TLabel").grid(
            row=2, column=0, sticky="w", pady=8, padx=(0, 10)
        )
        self.password_entry = ttk.Entry(self, width=28, show="*")
        self.password_entry.grid(row=2, column=1, pady=8, sticky="ew")

        login_btn = ttk.Button(self, text="Login", style="Login.TButton", command=self.login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=20)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Card.TFrame",
            background="#f5f1eb"
        )

        style.configure(
            "Custom.TLabel",
            background="#f5f1eb",
            foreground="#2c2c2c",
            font=("Georgia", 11)
        )

        style.configure(
            "Title.TLabel",
            background="#f5f1eb",
            foreground="#1f1f1f",
            font=("Georgia", 18, "bold")
        )

        style.configure(
            "Login.TButton",
            font=("Georgia", 11, "bold"),
            padding=8
        )

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password.")
            return

        success, message = AuthController.login(username, password)

        if success:
            messagebox.showinfo("Success", message)
            self.on_login_success()
        else:
            messagebox.showerror("Login Failed", message)