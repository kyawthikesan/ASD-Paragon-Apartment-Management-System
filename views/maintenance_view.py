import tkinter as tk
from tkinter import ttk, messagebox
from dao.maintenance_dao import MaintenanceDAO
from views.scheduleview import ScheduleView


class MaintenanceDashboardView(ttk.Frame):
    def __init__(self, parent, logout_callback=None, home_callback=None):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.dao = MaintenanceDAO()

        # Header
        top_bar = ttk.Frame(self, padding=12)
        top_bar.pack(fill="x")
        ttk.Label(top_bar, text="Maintenance Dashboard", font=("Arial", 18, "bold")).pack(side="left")

        if home_callback:
            ttk.Button(top_bar, text="Home", command=home_callback).pack(side="right", padx=6)
        if logout_callback:
            ttk.Button(top_bar, text="Logout", command=logout_callback).pack(side="right", padx=6)

        # Treeview Table
        self.tree = ttk.Treeview(self, columns=("ID", "CompID", "Staff", "Status", "Cost", "Hours"), show='headings')
        for col in ("ID", "CompID", "Staff", "Status", "Cost", "Hours"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Control Panel
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_data).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="📅 Schedule/Update", command=self.open_scheduler).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="📊 Cost Report", command=self.show_report).grid(row=0, column=2, padx=5)

        self.load_data()

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.dao.get_all_requests():
            request_id = row.get("requestID", row.get("id"))
            complaint_id = row.get("complaint_id", row.get("apartmentID", "-"))
            staff_name = row.get("staff_name", "-")
            status = row.get("status", "Open")
            cost = float(row.get("cost", 0) or 0)
            hours = int(row.get("hours_spent", 0) or 0)
            self.tree.insert(
                "",
                tk.END,
                values=(request_id, complaint_id, staff_name, status, f"{cost:.2f}", hours),
            )

    def open_scheduler(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Error", "Select a record")
        val = self.tree.item(sel)['values']
        ScheduleView(self, self.dao, val[0], val, self.load_data)

    def show_report(self):
        # Satisfies "Generate maintenance cost reports" requirement 
        total, hours, count = self.dao.get_cost_report_data()
        report = f"Resolved Tasks: {count}\nTotal Cost: £{total if total else 0:.2f}\nTotal Labor: {hours if hours else 0} hrs"
        messagebox.showinfo("Maintenance Cost Report", report)


class MaintenanceView(MaintenanceDashboardView):
    """Backward-compatible alias for older imports."""
    pass

if __name__ == "__main__":
    root = tk.Tk()
    app = MaintenanceDashboardView(root)
    root.mainloop()
