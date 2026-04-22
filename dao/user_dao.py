from datetime import datetime
import sqlite3
from database.db_manager import DBManager
from utils.security import hash_password


class UserDAO:
    PERMISSION_KEYS = [
        "register_tenants",
        "manage_payments",
        "log_maintenance",
        "generate_reports",
        "manage_user_accounts",
    ]

    DEFAULT_ROLE_PERMISSIONS = {
        "admin": {
            "register_tenants": 1,
            "manage_payments": 1,
            "log_maintenance": 1,
            "generate_reports": 1,
            "manage_user_accounts": 1,
        },
        "finance": {
            "register_tenants": 0,
            "manage_payments": 1,
            "log_maintenance": 0,
            "generate_reports": 1,
            "manage_user_accounts": 0,
        },
        "front_desk": {
            "register_tenants": 1,
            "manage_payments": 0,
            "log_maintenance": 1,
            "generate_reports": 0,
            "manage_user_accounts": 0,
        },
        "maintenance": {
            "register_tenants": 0,
            "manage_payments": 0,
            "log_maintenance": 1,
            "generate_reports": 0,
            "manage_user_accounts": 0,
        },
        "manager": {
            "register_tenants": 1,
            "manage_payments": 1,
            "log_maintenance": 1,
            "generate_reports": 1,
            "manage_user_accounts": 1,
        },
    }


    @staticmethod
    def seed_roles() -> None:
        roles = ["admin", "front_desk", "finance", "maintenance", "manager"]

        conn = DBManager.get_connection()
        try:
            for role in roles:
                conn.execute(
                    "INSERT OR IGNORE INTO roles (role_name) VALUES (?)",
                    (role,)
                )
            for role_name, permissions in UserDAO.DEFAULT_ROLE_PERMISSIONS.items():
                role_row = conn.execute(
                    "SELECT id FROM roles WHERE role_name = ?",
                    (role_name,)
                ).fetchone()
                if role_row is None:
                    continue
                for permission_key in UserDAO.PERMISSION_KEYS:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_key, allowed)
                        VALUES (?, ?, ?)
                        """,
                        (
                            role_row["id"],
                            permission_key,
                            int(permissions.get(permission_key, 0)),
                        )
                    )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def create_user(full_name: str, username: str, password: str,
                    role_name: str, location: str | None = None,
                    is_active: int = 1) -> None:

        conn = DBManager.get_connection()
        try:
            role = conn.execute(
                "SELECT id FROM roles WHERE role_name = ?",
                (role_name,)
            ).fetchone()

            if role is None:
                raise ValueError(f"Role '{role_name}' does not exist.")

            try:
                conn.execute("""
                    INSERT INTO users (
                        full_name,
                        username,
                        password_hash,
                        role_id,
                        location,
                        is_active,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name,
                    username,
                    hash_password(password),
                    role["id"],
                    location,
                    is_active,
                    datetime.now().isoformat(timespec="seconds")
                ))
            except sqlite3.IntegrityError as error:
                if "users.username" in str(error) or "UNIQUE constraint failed: users.username" in str(error):
                    raise ValueError("Username already exists.") from error
                raise

            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_roles():
        conn = DBManager.get_connection()
        try:
            rows = conn.execute(
                "SELECT role_name FROM roles ORDER BY role_name"
            ).fetchall()
            return [row["role_name"] for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_user_by_username(username: str):
        conn = DBManager.get_connection()
        try:
            return conn.execute("""
                SELECT u.id,
                       u.full_name,
                       u.username,
                       u.password_hash,
                       u.location,
                       u.is_active,
                       u.last_login,
                       r.role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE LOWER(u.username) = LOWER(?)
            """, (username,)).fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_all_users():
        conn = DBManager.get_connection()
        try:
            return conn.execute("""
                SELECT u.id,
                       u.full_name,
                       u.username,
                       r.role_name,
                       u.location,
                       u.is_active,
                       u.last_login
                FROM users u
                JOIN roles r ON u.role_id = r.id
                ORDER BY u.id
            """).fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_active_maintenance_staff(city: str | None = None):
        conn = DBManager.get_connection()
        try:
            query = """
                SELECT
                    u.id,
                    u.full_name,
                    u.username,
                    u.location
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE LOWER(r.role_name) = 'maintenance'
                  AND u.is_active = 1
            """
            params = []
            if city and str(city).strip():
                query += " AND LOWER(TRIM(COALESCE(u.location, ''))) = LOWER(TRIM(?))"
                params.append(str(city).strip())
            query += " ORDER BY u.full_name"
            return conn.execute(query, tuple(params)).fetchall()
        finally:
            conn.close()

    @staticmethod
    def update_last_login(user_id: int) -> None:
        conn = DBManager.get_connection()
        try:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(timespec="seconds"), user_id),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def deactivate_user(user_id: int) -> None:
        conn = DBManager.get_connection()
        try:
            conn.execute(
                "UPDATE users SET is_active = 0 WHERE id = ?",
                (user_id,)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update_user(user_id: int, full_name: str, username: str, role_name: str,
                    location: str | None, is_active: int, password: str | None = None) -> None:
        conn = DBManager.get_connection()
        try:
            role = conn.execute(
                "SELECT id FROM roles WHERE role_name = ?",
                (role_name,)
            ).fetchone()
            if role is None:
                raise ValueError(f"Role '{role_name}' does not exist.")

            params = [full_name, username, role["id"], location, is_active]
            set_clause = """
                full_name = ?,
                username = ?,
                role_id = ?,
                location = ?,
                is_active = ?
            """

            # Password is optional during edit; keep current hash when left blank.
            if password:
                set_clause += ", password_hash = ?"
                params.append(hash_password(password))

            params.append(user_id)

            try:
                conn.execute(
                    f"UPDATE users SET {set_clause} WHERE id = ?",
                    tuple(params)
                )
            except sqlite3.IntegrityError as error:
                if "users.username" in str(error) or "UNIQUE constraint failed: users.username" in str(error):
                    raise ValueError("Username already exists.") from error
                raise

            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_role_permissions() -> dict[str, dict[str, int]]:
        conn = DBManager.get_connection()
        try:
            rows = conn.execute(
                """
                SELECT r.role_name, rp.permission_key, rp.allowed
                FROM roles r
                LEFT JOIN role_permissions rp ON rp.role_id = r.id
                """
            ).fetchall()

            result = {
                role: {perm: int(UserDAO.DEFAULT_ROLE_PERMISSIONS.get(role, {}).get(perm, 0))
                       for perm in UserDAO.PERMISSION_KEYS}
                for role in UserDAO.DEFAULT_ROLE_PERMISSIONS.keys()
            }

            for row in rows:
                role_name = str(row["role_name"]).strip().lower()
                permission_key = row["permission_key"]
                if role_name not in result:
                    result[role_name] = {perm: 0 for perm in UserDAO.PERMISSION_KEYS}
                if permission_key in UserDAO.PERMISSION_KEYS:
                    result[role_name][permission_key] = int(row["allowed"] or 0)
            return result
        finally:
            conn.close()

    @staticmethod
    def update_role_permissions(permissions_matrix: dict[str, dict[str, int]]) -> None:
        conn = DBManager.get_connection()
        try:
            for role_name, permissions in permissions_matrix.items():
                role_row = conn.execute(
                    "SELECT id FROM roles WHERE role_name = ?",
                    (role_name,)
                ).fetchone()
                if role_row is None:
                    continue

                for permission_key in UserDAO.PERMISSION_KEYS:
                    allowed = int(bool(permissions.get(permission_key, 0)))
                    conn.execute(
                        """
                        INSERT INTO role_permissions (role_id, permission_key, allowed)
                        VALUES (?, ?, ?)
                        ON CONFLICT(role_id, permission_key)
                        DO UPDATE SET allowed = excluded.allowed
                        """,
                        (role_row["id"], permission_key, allowed)
                    )
            conn.commit()
        finally:
            conn.close()
