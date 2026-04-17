from datetime import datetime
from database.db_manager import DBManager
from utils.security import hash_password


class UserDAO:

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

            conn.commit()
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
                       r.role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = ?
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
                       u.is_active
                FROM users u
                JOIN roles r ON u.role_id = r.id
                ORDER BY u.id
            """).fetchall()
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