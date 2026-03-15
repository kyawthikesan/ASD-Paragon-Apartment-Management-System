from database.database import create_tables, seed_admin
import tkinter as tk
from views.login_view import LoginView


def main():
    create_tables()
    seed_admin()
    root = tk.Tk()
    root.title("Paragon Apartment Management System (PAMS)")
    root.geometry("900x600")

    LoginView(root)

    root.mainloop()

if __name__ == "__main__":
    main()