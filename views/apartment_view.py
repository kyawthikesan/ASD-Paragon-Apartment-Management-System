import tkinter as tk
from tkinter import messagebox
from controllers.apartment_controller import ApartmentController


class ApartmentView:

    def __init__(self, root):

        frame = tk.Frame(root)
        frame.pack(pady=20)

        tk.Button(root, text="Back", command=lambda: self.go_back(root)).pack()

        tk.Label(frame, text="Apartment Management", font=("Arial", 18)).grid(row=0, columnspan=2, pady=10)

        tk.Label(frame, text="City").grid(row=1, column=0)
        self.city = tk.Entry(frame)
        self.city.grid(row=1, column=1)

        tk.Label(frame, text="Type").grid(row=2, column=0)
        self.type = tk.Entry(frame)
        self.type.grid(row=2, column=1)

        tk.Label(frame, text="Rent").grid(row=3, column=0)
        self.rent = tk.Entry(frame)
        self.rent.grid(row=3, column=1)

        tk.Label(frame, text="Status").grid(row=4, column=0)
        self.status = tk.Entry(frame)
        self.status.grid(row=4, column=1)

        tk.Button(frame, text="Add Apartment", command=self.add_apartment).grid(row=5, columnspan=2, pady=10)

        self.listbox = tk.Listbox(root, width=70)
        self.listbox.pack(pady=20)

        self.load_apartments()

    def add_apartment(self):

        city = self.city.get()
        apt_type = self.type.get()
        rent = self.rent.get()
        status = self.status.get()

        ApartmentController.add_apartment(city, apt_type, rent, status)

        messagebox.showinfo("Success", "Apartment Added")

        self.load_apartments()

    def load_apartments(self):

        self.listbox.delete(0, tk.END)

        apartments = ApartmentController.get_all_apartments()

        for a in apartments:
            self.listbox.insert(tk.END, f"ID:{a[0]} | {a[1]} | {a[2]} | Rent:{a[3]} | {a[4]}")

    def go_back(self, root):

        from views.dashboard_view import DashboardView

        for widget in root.winfo_children():
            widget.destroy()

        DashboardView(root)