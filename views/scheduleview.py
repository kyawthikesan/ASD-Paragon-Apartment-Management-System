import tkinter as tk
from tkinter import ttk, messagebox

class ScheduleView(tk.Toplevel):
    def __init__(self, parent, dao, req_id, current_values, refresh_callback):
        super().__init__(parent)
        self.dao = dao
        self.req_id = req_id
        self.callback = refresh_callback
        self.title(f"Schedule Maintenance #{req_id}")
        self.geometry("300x400")

        tk.Label(self, text="Assign Staff:").pack(pady=5)
        self.staff_ent = ttk.Entry(self)
        self.staff_ent.insert(0, current_values[2])
        self.staff_ent.pack()

        tk.Label(self, text="Status:").pack(pady=5)
        self.status_cb = ttk.Combobox(self, values=["Pending", "Assigned", "In Progress", "Resolved"])
        self.status_cb.set(current_values[3])
        self.status_cb.pack()

        tk.Label(self, text="Cost (£):").pack(pady=5)
        self.cost_ent = ttk.Entry(self)
        self.cost_ent.insert(0, current_values[4])
        self.cost_ent.pack()

        tk.Label(self, text="Hours:").pack(pady=5)
        self.hour_ent = ttk.Entry(self)
        self.hour_ent.insert(0, current_values[5])
        self.hour_ent.pack()

        ttk.Button(self, text="Save & Close", command=self.save).pack(pady=20)

    def save(self):
        try:
            self.dao.update_maintenance(self.req_id, self.staff_ent.get(), "2026-04-21", 
                                        self.status_cb.get(), float(self.cost_ent.get()), int(self.hour_ent.get()))
            self.callback()
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid Cost or Hours")