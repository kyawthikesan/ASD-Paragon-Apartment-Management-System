import tkinter as tk
from tkinter import ttk, messagebox
from maintenance_dao import MaintenanceDAO
from scheduleview import ScheduleView

class MaintenanceView:
    def __init__(self, root):
        self.root = root
        self.root.title("UWE Maintenance System")
        self.root.geometry("900x600")
        self.dao = MaintenanceDAO()

        # Header
        tk.Label(root, text="Maintenance Dashboard", font=("Arial", 20), bg="#2c3e50", fg="white", pady=15).pack(fill=tk.X)

        # Treeview Table
        self.tree = ttk.Treeview(root, columns=("ID", "CompID", "Staff", "Status", "Cost", "Hours"), show='headings')
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
        for item in self.tree.get_children(): self.tree.delete(item)
        for row in self.dao.get_all_requests():
            self.tree.insert("", tk.END, values=(row[0], row[1], row[2], row[4], f"{row[5]:.2f}", row[6]))

    def open_scheduler(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Error", "Select a record")
        val = self.tree.item(sel)['values']
        ScheduleView(self.root, self.dao, val[0], val, self.load_data)

    def show_report(self):
        # Satisfies "Generate maintenance cost reports" requirement 
        total, hours, count = self.dao.get_cost_report_data()
        report = f"Resolved Tasks: {count}\nTotal Cost: £{total if total else 0:.2f}\nTotal Labor: {hours if hours else 0} hrs"
        messagebox.showinfo("Maintenance Cost Report", report)

if __name__ == "__main__":
    root = tk.Tk()
    app = MaintenanceView(root)
    root.mainloop()