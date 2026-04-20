from tkinter import ttk


class MaintenanceDashboardView(ttk.Frame):
    def __init__(self, parent, logout_callback=None, home_callback=None):
        super().__init__(parent)
        self.logout_callback = logout_callback
        self.home_callback = home_callback

        self.pack(fill="both", expand=True)

        top_bar = ttk.Frame(self, padding=12)
        top_bar.pack(fill="x")

        ttk.Label(
            top_bar,
            text="Maintenance Dashboard",
            font=("Arial", 16, "bold")
        ).pack(side="left")

        if self.home_callback:
            ttk.Button(
                top_bar,
                text="← Home",
                command=self.home_callback
            ).pack(side="right", padx=6)

        if self.logout_callback:
            ttk.Button(
                top_bar,
                text="Logout",
                command=self.logout_callback
            ).pack(side="right", padx=6)

        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)

        ttk.Label(
            body,
            text="Maintenance Dashboard",
            font=("Arial", 16, "bold")
        ).pack(pady=20)