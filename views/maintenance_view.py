from tkinter import ttk

class MaintenanceDashboardView(ttk.Frame):
    def __init__(self, parent, logout_callback=None):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        ttk.Label(self, text="Maintenance Dashboard", font=("Arial", 16, "bold")).pack(pady=20)

        if logout_callback:
            ttk.Button(self, text="Logout", command=logout_callback).pack(pady=10)