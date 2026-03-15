# Paragon Apartment Management System (PAMS)

## Module Information
**Module:** Applied System Design  
**Project Title:** Paragon Apartment Management System (PAMS)  
**Academic Year:** 2025/2026  

## Project Overview
The Paragon Apartment Management System (PAMS) is a desktop-based software application developed to support the management of apartment-related operations. The system provides an organised and user-friendly platform for managing tenants, apartments, and lease records while demonstrating the practical application of system analysis, design, and implementation principles.

This project was developed as a group assignment and focuses on applying software development methodologies, object-oriented design, modular programming, graphical user interface development, and database integration.

## Objectives
The main objectives of this project are:
- To design and develop a functional apartment management system
- To provide role-based access through a login system
- To manage core records such as tenants, apartments, and leases
- To demonstrate good system structure using Python modules, controllers, views, and database components
- To apply concepts learned in system analysis and design into a practical software solution

## System Features
The system currently includes the following features:
- Secure login interface
- Role-based dashboard access
- Tenant management
- Apartment management
- Lease management
- Organised graphical user interface using Tkinter
- Database storage using SQLite

## Technologies Used
- **Programming Language:** Python
- **GUI Framework:** Tkinter
- **Database:** SQLite
- **Development Approach:** Modular and object-oriented design

## System Structure
The project is organised into multiple components to improve readability, maintainability, and scalability:

- **Main Program** – starts the application and initializes the database
- **Database Layer** – handles database connection, table creation, and seed data
- **Controllers** – manage business logic such as login authentication
- **Views** – provide the graphical interface for users to interact with the system

## Project Files
```text
PAMS/
│── main.py
│── database/
│   └── database.py
│── controllers/
│   └── login_controller.py
│── views/
│   ├── login_view.py
│   ├── dashboard_view.py
│   ├── tenant_view.py
│   ├── apartment_view.py
│   └── lease_view.py

## Team Members and Roles
This project was completed by a group of four members:
**Kyaw Thike San** – Project Lead, System Architect, and Integration Lead
Responsible for leading the project, coordinating group tasks, planning the system structure, supporting the integration of system components, and ensuring the final application aligned with project requirements.
[Member 2 Name] – UI/Frontend Developer
Responsible for designing and implementing the graphical user interface, improving layout, and enhancing user interaction.
[Member 3 Name] – Backend and Database Developer
Responsible for database design, data handling, query implementation, and backend logic.
[Member 4 Name] – Testing and Documentation Lead
Responsible for testing system functions, identifying bugs, supporting debugging, and preparing documentation.


## To run the project:
- Ensure Python 3 is installed on your computer
- Download or clone the project files
- Open the project folder in your preferred code editor or terminal
- Run the application using:
- python main.py

## Default Login Accounts
The system includes the following default user accounts for testing:

** Administrator **
Username: admin
Password: admin123

** Front-desk Staff **
Username: frontdesk1
Password: fd123

** Finance Manager **
Username: finance1
Password: fin123

** Maintenance Staff **
Username: maint1
Password: mt123

** Manager **
Username: manager1
Password: mgr123

## Future Improvements
The following features may be implemented in future versions:
- Payment management
- Maintenance request management
- Report generation
- Improved validation and error handling
- Enhanced security for login credentials
- Search and filtering functions
- More detailed user role permissions

## Conclusion
The Paragon Apartment Management System (PAMS) demonstrates the successful development of a desktop application that applies key concepts from applied system design. The project reflects teamwork, modular design, GUI implementation, and database integration while addressing the practical needs of apartment management.
Academic Use
This project was developed for academic purposes as part of a university group assignment.


