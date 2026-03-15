import tkinter as tk
from tkinter import messagebox
from controllers.login_controller import LoginController
from views.dashboard_view import DashboardView


class LoginView:

    def __init__(self, root):

        self.root = root

        frame = tk.Frame(root)
        frame.pack(pady=150)

        tk.Label(frame, text="Login to PAMS", font=("Arial", 16)).grid(row=0, columnspan=2, pady=10)

        tk.Label(frame, text="Username").grid(row=1, column=0)
        self.username_entry = tk.Entry(frame)
        self.username_entry.grid(row=1, column=1)

        tk.Label(frame, text="Password").grid(row=2, column=0)
        self.password_entry = tk.Entry(frame, show="*")
        self.password_entry.grid(row=2, column=1)

        tk.Button(frame, text="Login", command=self.login).grid(row=3, columnspan=2, pady=10)

    def login(self):

        username = self.username_entry.get()
        password = self.password_entry.get()

        role = LoginController.authenticate(username, password)

        if role:
            messagebox.showinfo("Success", "Login Successful")

            for widget in self.root.winfo_children():
                widget.destroy()

            DashboardView(self.root)

        else:
            messagebox.showerror("Error", "Invalid login")