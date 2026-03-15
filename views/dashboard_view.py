import tkinter as tk
from tkinter import messagebox

from views.tenant_view import TenantView
from views.apartment_view import ApartmentView
from views.lease_view import LeaseView


class DashboardView:
    def __init__(self, root, role: str):
        self.root = root
        self.role = self._normalize_role(role)

        self.frame = tk.Frame(root)
        self.frame.pack(fill="both", expand=True, pady=40)

        tk.Label(self.frame, text="PAMS Dashboard", font=("Arial", 20)).pack(pady=10)
        tk.Label(self.frame, text=f"Logged in as: {self.role}", font=("Arial", 10)).pack(pady=5)

        allowed = self._allowed_features(self.role)

        if "tenant" in allowed:
            tk.Button(self.frame, text="Tenant Management", width=25,
                      command=self.open_tenant).pack(pady=5)

        if "apartment" in allowed:
            tk.Button(self.frame, text="Apartment Management", width=25,
                      command=self.open_apartment).pack(pady=5)

        if "lease" in allowed:
            tk.Button(self.frame, text="Lease Management", width=25,
                      command=self.open_lease).pack(pady=5)

        if "payments" in allowed:
            tk.Button(self.frame, text="Payments", width=25,
                      command=self.open_payments).pack(pady=5)

        if "maintenance" in allowed:
            tk.Button(self.frame, text="Maintenance", width=25,
                      command=self.open_maintenance).pack(pady=5)

        if "reports" in allowed:
            tk.Button(self.frame, text="Reports", width=25,
                      command=self.open_reports).pack(pady=5)

        tk.Button(self.frame, text="Logout", width=25, command=self.logout).pack(pady=20)

    # ---------- RBAC helpers ----------
    def _normalize_role(self, role: str) -> str:
        r = (role or "").strip().lower()

        if r in {"admin", "administrator"}:
            return "Administrator"
        if r in {"frontdesk", "front-desk", "front desk", "frontdeskstaff", "front-desk staff"}:
            return "Front-desk Staff"
        if r in {"finance", "finance manager", "financemanager"}:
            return "Finance Manager"
        if r in {"maintenance", "maintenance staff", "maintenancestaff"}:
            return "Maintenance Staff"
        if r in {"manager"}:
            return "Manager"

        return role  # fallback

    def _allowed_features(self, role: str) -> set[str]:
        # Adjust as your team agrees / matches your UML + FRs
        permissions = {
            "Front-desk Staff": {"tenant", "lease", "apartment", "maintenance"},
            "Finance Manager": {"payments", "reports"},
            "Maintenance Staff": {"maintenance"},
            "Administrator": {"tenant", "lease", "apartment", "payments", "maintenance", "reports"},
            "Manager": {"reports"},  # add more if your teacher wants manager access to everything
        }
        return permissions.get(role, set())

    # ---------- Navigation ----------
    def _clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def open_tenant(self):
        self._clear_root()
        TenantView(self.root)

    def open_apartment(self):
        self._clear_root()
        ApartmentView(self.root)

    def open_lease(self):
        self._clear_root()
        LeaseView(self.root)

    # Placeholders (so app doesn't crash if not implemented)
    def open_payments(self):
        messagebox.showinfo("Payments", "Payments screen not implemented yet.")

    def open_maintenance(self):
        messagebox.showinfo("Maintenance", "Maintenance screen not implemented yet.")

    def open_reports(self):
        messagebox.showinfo("Reports", "Reports screen not implemented yet.")

    def logout(self):
        # Lazy import to avoid circular imports
        from views.login_view import LoginView

        self._clear_root()
        LoginView(self.root)