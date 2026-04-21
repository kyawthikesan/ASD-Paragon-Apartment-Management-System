from dao.user_dao import UserDAO
from utils.security import verify_password


class AuthController:
    current_user = None
    FEATURE_ACCESS = {
        "user_management": {"admin"},
        "tenant_management": {"admin", "manager", "front_desk"},
        "apartment_management": {"admin", "manager", "front_desk"},
        "lease_management": {"admin", "manager", "front_desk"},
        "finance_dashboard": {"admin", "finance"},
        "maintenance_dashboard": {"maintenance"},
        # Compatibility keys used by some views/controllers.
        "payment_management": {"admin", "finance"},
        "reports": {"admin", "finance"},
        "maintenance_management": {"admin", "manager", "front_desk", "maintenance"},
    }

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
    def is_admin(role: str | None = None) -> bool:
        role_name = role or AuthController.get_current_role()
        return role_name == "admin"

    @staticmethod
    def get_current_location() -> str | None:
        user = AuthController.current_user
        if not user:
            return None
        try:
            location = str(user["location"]).strip()
        except Exception:
            return None
        return location or None

    @staticmethod
    def get_city_scope(selected_city: str | None = None) -> str | None:
        """
        Returns effective city scope for data access.
        - admin: None (all cities) unless a specific city is selected
        - non-admin: always restricted to the user's own location
        """
        if AuthController.is_admin():
            city = (selected_city or "").strip()
            if city and city.lower() not in {"all cities", "all"}:
                return city
            return None
        return AuthController.get_current_location()

    @staticmethod
    def can_access_city(city: str | None, role: str | None = None) -> bool:
        if not city:
            return True
        if AuthController.is_admin(role):
            return True
        current_location = AuthController.get_current_location()
        return bool(current_location and current_location.strip().lower() == city.strip().lower())

    @staticmethod
    def can_access_feature(feature_key: str, role: str | None = None) -> bool:
        role_name = role or AuthController.get_current_role()
        if not role_name:
            return False
        return role_name in AuthController.FEATURE_ACCESS.get(feature_key, set())