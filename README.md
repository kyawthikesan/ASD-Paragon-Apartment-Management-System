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
- Centralized RBAC feature guards
- Tenant management
- Apartment management
- Lease management
- Finance dashboard (payment recording and status tracking)
- Maintenance dashboard (request creation and status tracking)
- Unified premium dashboard style aligned with login theme
- Responsive layout behavior for different window sizes
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
│   ├── db_manager.py
│   └── schema.sql
│── controllers/
│   ├── auth_controller.py
│   ├── payment_controller.py
│   ├── maintenance_controller.py
│   └── ...
│── dao/
│   ├── user_dao.py
│   ├── tenant_dao.py
│   ├── apartment_dao.py
│   ├── lease_dao.py
│   ├── payment_dao.py
│   └── maintenance_dao.py
│── views/
│   ├── login_view.py
│   ├── dashboard_view.py
│   ├── tenant_view.py
│   ├── apartment_view.py
│   ├── lease_view.py
│   ├── payment_view.py
│   └── maintenance_view.py
│── tests/
│   ├── test_auth.py
│   ├── test_user_dao.py
│   ├── test_member2.py
│   ├── test_payment_maintenance.py
│   └── test_navigation_integration.py
```

## Rubric Mapping (Implementation + Testing)
This section maps completed features to the assessment criteria.

- Implementation (business logic + GUI + DB integration)
  - Login authentication and role-based routing are fully implemented.
  - RBAC guards are enforced in navigation and module access.
  - Admin user management supports create, view, edit, and deactivate.
  - Tenant, apartment, and lease modules are integrated with SQLite.
  - Finance and maintenance dashboards are implemented with create/list/update workflows.
  - Validation and clear user-facing error messages are included across core flows.

- Testing (scenario coverage)
  - Auth tests cover valid login, invalid login, incorrect password, and inactive users.
  - RBAC tests cover role/feature access decisions.
  - Navigation integration tests cover role routing and guard behavior on denied paths.
  - DAO tests cover user create/update/deactivate and duplicate username handling.
  - Finance and maintenance tests cover create and status update flows.
  - Current automated suite status: `27 tests passing` via `python3 -m unittest discover -s tests -p "test_*.py"`.

## Team Members and Roles
This project was completed by a group of four members:
**Shune Pyae Pyae Aung** – Project Lead, System Architect, and Integration Lead
Responsible for leading the project, dividing tasks among team members, coordinating implementation milestones, planning the system structure, supporting module integration, and ensuring the final application aligned with assessment requirements.
**Kyaw Thike San** – UI/Frontend Developer
Responsible for designing and implementing key graphical user interface components, improving layout, and enhancing user interaction.
**Nang Phwe Hleng Hun** – Backend and Database Developer
Responsible for database design, data handling, query implementation, and backend logic.
[Member 4 Name] – Testing and Documentation Lead
Responsible for testing system functions, identifying bugs, supporting debugging, and preparing documentation.


## Setup Instructions

### 1. Clone or download the project
Clone the repository or download the ZIP file, then open the project folder.

```bash
git clone <your-repository-url>
cd ASD-Paragon-Apartment-Management-System-PAMS-
2. Create a virtual environment
macOS / Linux
python3 -m venv venv
source venv/bin/activate
Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

If PowerShell blocks activation, run:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
3. Install the required packages
pip install -r requirements.txt
4. Run the application
python main.py
5. Database notes
The system uses a local SQLite database file called pams.db
If pams.db does not already exist, the application will automatically initialise the database
Some seed data may also be loaded from database/seed.sql

## Default Login Accounts
The system includes the following default user accounts for testing:

** Administrator **
Username: admin
Password: admin123


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
