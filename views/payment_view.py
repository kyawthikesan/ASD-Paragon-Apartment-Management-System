import tkinter as tk
from tkinter import ttk

class FinanceDashboardView(ttk.Frame):
    def __init__(self, parent, logout_callback=None):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        ttk.Label(self, text="Finance Dashboard").pack(pady=20)

        if logout_callback:
            ttk.Button(self, text="Logout", command=logout_callback).pack(pady=10)