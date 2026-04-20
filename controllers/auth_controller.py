from dao.user_dao import UserDAO
from utils.security import verify_password


class AuthController:
    current_user = None

    @staticmethod
    def login(username: str, password: str):
        user = UserDAO.get_user_by_username(username)

        if user is None:
            return False, "User not found."

        if user["is_active"] != 1:
            return False, "Account is inactive."

        if not verify_password(password, user["password_hash"]):
            return False, "Incorrect password."

        AuthController.current_user = user
        return True, f"Welcome {user['full_name']}"

    @staticmethod
    def logout() -> None:
        AuthController.current_user = None

    @staticmethod
    def get_current_role() -> str | None:
        if AuthController.current_user:
            return AuthController.current_user["role_name"]
        return None

    @staticmethod
    def can_manage_users() -> bool:
        return AuthController.get_current_role() == "admin"

    @staticmethod
    def can_access_feature(feature_key: str, role: str | None = None) -> bool:
        role_name = role or AuthController.get_current_role()

        permissions = {
            "admin": {
                "user_management",
                "tenant_management",
                "apartment_management",
                "lease_management",
                "payment_management",
                "maintenance_management",
                "reports",
            },
            "manager": {
                "tenant_management",
                "apartment_management",
                "lease_management",
                "payment_management",
                "maintenance_management",
                "reports",
            },
            "front_desk": {
                "tenant_management",
                "apartment_management",
                "lease_management",
                "maintenance_management",
            },
            "finance": {
                "payment_management",
                "reports",
            },
            "maintenance": {
                "maintenance_management",
            },
        }

        return feature_key in permissions.get(role_name, set())