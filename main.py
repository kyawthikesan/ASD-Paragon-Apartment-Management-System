from database.database import create_tables, seed_default_users
import tkinter as tk
from views.login_view import LoginView


def main():
    create_tables()
    seed_default_users()
    
    root = tk.Tk()
    root.title("Paragon Apartment Management System (PAMS)")
    root.geometry("900x600")

    LoginView(root)

    root.mainloop()

if __name__ == "__main__":
    main()