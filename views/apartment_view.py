import tkinter as tk
from tkinter import ttk, messagebox
from controllers.apartment_controller import ApartmentController
from controllers.auth_controller import AuthController
from dao.location_dao import LocationDAO
from views.premium_shell import PremiumAppShell


class ApartmentView(tk.Frame):

    def __init__(self, parent, back_callback):
        super().__init__(parent, bg="#F9F5EE")
        self.pack(fill="both", expand=True)
        self.is_admin = AuthController.is_admin()
        self.city_scope = AuthController.get_city_scope()

        role = AuthController.get_current_role()
        nav_sections = [
            {"title": "Overview", "items": [{"label": "Dashboard", "action": back_callback, "icon": "⌂"}]},
            {
                "title": "Management",
                "items": [
                    {"label": "Tenants", "action": back_callback, "icon": "👤"},
                    {"label": "Apartments", "action": lambda: None, "icon": "▦"},
                ],
            },
        ]
        if AuthController.can_access_feature("lease_management", role):
            nav_sections[1]["items"].append({"label": "Leases", "action": back_callback, "icon": "📄"})

        shell = PremiumAppShell(
            self,
            page_title="Apartment Management",
            on_logout=back_callback,
            active_nav="Apartments",
            nav_sections=nav_sections,
            footer_action_label="Back to Dashboard",
            search_placeholder="Search units...",
        )
        content = shell.content

        apartments = ApartmentController.get_all_apartments(city=self.city_scope)
        total_units = len(apartments)
        avg_rent = int(sum(float(a["rent"]) for a in apartments) / total_units) if total_units else 0
        cities = len({a["city"] for a in apartments}) if apartments else 0

        stat_row = tk.Frame(content, bg="#F9F5EE")
        stat_row.pack(fill="x", pady=(0, 10))
        for col in range(3):
            stat_row.grid_columnconfigure(col, weight=1)
        stats = [
            ("TOTAL UNITS", str(total_units)),
            ("AVG RENT", f"£{avg_rent}"),
            ("CITIES", str(cities)),
        ]
        for idx, (label, value) in enumerate(stats):
            card = tk.Frame(stat_row, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E4D8C6", padx=14, pady=10)
            card.grid(row=0, column=idx, sticky="ew", padx=5)
            tk.Label(card, text=label, bg="#FFFFFF", fg="#9D8B73", font=("Segoe UI", 9, "bold")).pack(anchor="w")
            tk.Label(card, text=value, bg="#FFFFFF", fg="#2F2A23", font=("Georgia", 19, "bold")).pack(anchor="w", pady=(2, 0))

        # FORM
        form_frame = ttk.LabelFrame(content, text="Apartment Details", padding=15)
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
        table_frame = ttk.LabelFrame(content, text="Apartments", padding=10)
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

        columns = ("ID", "Location", "Type", "Rent", "Rooms")

        self.table = ttk.Treeview(container, columns=columns, show="headings")

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=140, stretch=True, anchor="center")

        self.table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.table.yview)
        scrollbar.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.bind("<<TreeviewSelect>>", self.fill_fields)

        self.load_apartments()

    def load_apartments(self):
        for row in self.table.get_children():
            self.table.delete(row)

        apartments = ApartmentController.get_all_apartments(city=self.city_scope)

        for apt in apartments:
            self.table.insert("", tk.END, values=(
                apt["apartmentID"],
                apt["city"],
                apt["type"],
                apt["rent"],
                apt["rooms"]
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
        if not AuthController.can_access_city(selected_city):
            messagebox.showerror("Restricted", "You can only manage apartments in your assigned location.")
            return
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
        if not AuthController.can_access_city(selected_city):
            messagebox.showerror("Restricted", "You can only manage apartments in your assigned location.")
            return
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

        results = ApartmentController.search_apartment(keyword, city=self.city_scope)

        for apt in results:
            self.table.insert("", tk.END, values=(
                apt["apartmentID"],
                apt["city"],  
                apt["type"],
                apt["rent"],
                apt["rooms"]
            ))

    def load_locations(self):
        locations = LocationDAO.get_all_locations()
        if not self.is_admin and self.city_scope:
            locations = [loc for loc in locations if str(loc["city"]).strip() == self.city_scope]

        # store mapping: city → id
        self.location_map = {loc["city"]: loc["location_id"] for loc in locations}

        # show city names
        self.location_combo["values"] = list(self.location_map.keys())

        if locations:
            self.location_combo.current(0)  # select first by default
        if not self.is_admin:
            self.location_combo.configure(state="disabled")

    def clear_fields(self):
        self.location_combo.set("") 
        self.type.delete(0, tk.END)
        self.rent.delete(0, tk.END)
        self.rooms.delete(0, tk.END)

        self.update_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")
