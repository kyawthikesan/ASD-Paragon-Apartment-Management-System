import tkinter as tk
from tkinter import ttk, messagebox
from controllers.apartment_controller import ApartmentController
from dao.location_dao import LocationDAO


class ApartmentView(tk.Frame):

    def __init__(self, parent, back_callback):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Top
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x")

        ttk.Button(top_frame, text="← Back", command=back_callback).pack(side="left")
        ttk.Label(top_frame, text="Apartment Management", font=("Arial", 16, "bold")).pack(side="left", padx=20)

        # FORM
        form_frame = ttk.LabelFrame(main_frame, text="Apartment Details", padding=15)
        form_frame.pack(fill="x", pady=10)
        
        ttk.Label(form_frame, text="Location").grid(row=0, column=0, padx=10, pady=5)
        self.location_combo = ttk.Combobox(form_frame, state="readonly")
        self.location_combo.grid(row=0, column=1)
        self.load_locations() 

        ttk.Label(form_frame, text="Type").grid(row=1, column=0, padx=10, pady=5)
        self.type = ttk.Entry(form_frame)
        self.type.grid(row=1, column=1)

        ttk.Label(form_frame, text="Rent").grid(row=2, column=0, padx=10, pady=5)
        self.rent = ttk.Entry(form_frame)
        self.rent.grid(row=2, column=1)

        ttk.Label(form_frame, text="Rooms").grid(row=3, column=0, padx=10, pady=5)
        self.rooms = ttk.Entry(form_frame)
        self.rooms.grid(row=3, column=1)

        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Add", command=self.add_apartment).grid(row=0, column=0, padx=5)

        self.update_btn = ttk.Button(btn_frame, text="Update", command=self.update_apartment, state="disabled")
        self.update_btn.grid(row=0, column=1, padx=5)

        self.delete_btn = ttk.Button(btn_frame, text="Delete", command=self.delete_apartment, state="disabled")
        self.delete_btn.grid(row=0, column=2, padx=5)

        # TABLE
        table_frame = ttk.LabelFrame(main_frame, text="Apartments", padding=10)
        table_frame.pack(fill="both", expand=True)

        # Search
        search_frame = ttk.Frame(table_frame)
        search_frame.pack(fill="x")

        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", padx=5)

        ttk.Button(search_frame, text="Search", command=self.search_apartment).pack(side="left")
        ttk.Button(search_frame, text="Show All", command=self.load_apartments).pack(side="left")

        # Table container
        container = ttk.Frame(table_frame)
        container.pack(fill="both", expand=True)

        columns = ("ID", "Location", "Type", "Rent", "Rooms", "Status")

        self.table = ttk.Treeview(container, columns=columns, show="headings")

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=120, anchor="center")

        self.table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.table.yview)
        scrollbar.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.bind("<<TreeviewSelect>>", self.fill_fields)

        self.load_apartments()

    def load_apartments(self):
        for row in self.table.get_children():
            self.table.delete(row)

        apartments = ApartmentController.get_all_apartments()

        for apt in apartments:
            self.table.insert("", tk.END, values=(
                apt["apartmentID"],
                apt["city"],
                apt["type"],
                apt["rent"],
                apt["rooms"],
                apt["status"]
            ))

    def fill_fields(self, event):
        selected = self.table.selection()
        if not selected:
            return

        values = self.table.item(selected[0], "values")

        # set dropdown (city)
        self.location_combo.set(values[1])

        self.type.delete(0, tk.END)
        self.type.insert(0, values[2])

        self.rent.delete(0, tk.END)
        self.rent.insert(0, values[3])

        self.rooms.delete(0, tk.END)
        self.rooms.insert(0, values[4])

        self.update_btn.config(state="normal")
        self.delete_btn.config(state="normal")

    def add_apartment(self):
        selected_city = self.location_combo.get()
        location_id = self.location_map[selected_city]

        apt_type = self.type.get()
        rent = self.rent.get()
        rooms = self.rooms.get()

        if not selected_city or not apt_type or not rent or not rooms:
            messagebox.showerror("Error", "All fields are required")
            return

        ApartmentController.add_apartment(
            location_id,
            apt_type,
            rent,
            rooms
        )

        messagebox.showinfo("Success", "Apartment added")

        self.load_apartments()
        self.clear_fields()

    def update_apartment(self):
        selected = self.table.selection()
        if not selected:
            return

        apt_id = self.table.item(selected[0], "values")[0]

        selected_city = self.location_combo.get()
        location_id = self.location_map[selected_city]

        ApartmentController.update_apartment(
            apt_id,
            location_id,
            self.type.get(),
            self.rent.get(),
            self.rooms.get()
        )

        messagebox.showinfo("Updated", "Apartment updated")
        self.load_apartments()

    def delete_apartment(self):
        selected = self.table.selection()
        if not selected:
            return

        apt_id = self.table.item(selected[0], "values")[0]

        ApartmentController.delete_apartment(apt_id)
        messagebox.showinfo("Deleted", "Apartment deleted")
        self.load_apartments()

    def search_apartment(self):
        keyword = self.search_entry.get()

        for row in self.table.get_children():
            self.table.delete(row)

        results = ApartmentController.search_apartment(keyword)

        for apt in results:
            self.table.insert("", tk.END, values=(
                apt["apartmentID"],
                apt["city"],  
                apt["type"],
                apt["rent"],
                apt["rooms"],
                apt["status"]
            ))

    def load_locations(self):
        locations = LocationDAO.get_all_locations()

        # store mapping: city → id
        self.location_map = {loc["city"]: loc["location_id"] for loc in locations}

        # show city names
        self.location_combo["values"] = list(self.location_map.keys())

        if locations:
            self.location_combo.current(0)  # select first by default   

    def clear_fields(self):
        self.location_combo.set("") 
        self.type.delete(0, tk.END)
        self.rent.delete(0, tk.END)
        self.rooms.delete(0, tk.END)

        self.update_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")