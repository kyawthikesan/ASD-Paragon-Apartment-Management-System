import unittest
from unittest.mock import patch

from controllers.auth_controller import AuthController
from utils.security import hash_password, verify_password


class TestSecurity(unittest.TestCase):
    def test_hash_password_returns_string(self):
        result = hash_password("admin123")
        self.assertIsInstance(result, str)

    def test_verify_password_correct(self):
        hashed = hash_password("secret")
        self.assertTrue(verify_password("secret", hashed))

    def test_verify_password_incorrect(self):
        hashed = hash_password("secret")
        self.assertFalse(verify_password("wrong", hashed))


class TestAuthController(unittest.TestCase):
    def setUp(self):
        AuthController.logout()

    def tearDown(self):
        AuthController.logout()

    @patch("controllers.auth_controller.UserDAO.get_user_by_username")
    def test_login_user_not_found(self, mock_get_user):
        mock_get_user.return_value = None

        success, message = AuthController.login("missing", "any")

        self.assertFalse(success)
        self.assertEqual(message, "User not found.")
        self.assertIsNone(AuthController.current_user)

    @patch("controllers.auth_controller.UserDAO.get_user_by_username")
    def test_login_inactive_user(self, mock_get_user):
        mock_get_user.return_value = {
            "full_name": "Inactive User",
            "username": "inactive",
            "password_hash": hash_password("secret"),
            "is_active": 0,
            "role_name": "front_desk",
        }

        success, message = AuthController.login("inactive", "secret")

        self.assertFalse(success)
        self.assertEqual(message, "Account is inactive.")
        self.assertIsNone(AuthController.current_user)

    @patch("controllers.auth_controller.UserDAO.get_user_by_username")
    def test_login_wrong_password(self, mock_get_user):
        mock_get_user.return_value = {
            "full_name": "Front Desk User",
            "username": "frontdesk",
            "password_hash": hash_password("right-password"),
            "is_active": 1,
            "role_name": "front_desk",
        }

        success, message = AuthController.login("frontdesk", "wrong-password")

        self.assertFalse(success)
        self.assertEqual(message, "Incorrect password.")
        self.assertIsNone(AuthController.current_user)

    @patch("controllers.auth_controller.UserDAO.get_user_by_username")
    def test_login_success_sets_current_user(self, mock_get_user):
        mock_get_user.return_value = {
            "id": 7,
            "full_name": "Shune",
            "username": "shune",
            "password_hash": hash_password("admin123"),
            "is_active": 1,
            "role_name": "admin",
        }

        success, message = AuthController.login("shune", "admin123")

        self.assertTrue(success)
        self.assertEqual(message, "Welcome Shune")
        self.assertIsNotNone(AuthController.current_user)
        self.assertEqual(AuthController.get_current_role(), "admin")
        self.assertTrue(AuthController.can_manage_users())

    def test_logout_clears_current_user(self):
        AuthController.current_user = {"role_name": "admin"}

        AuthController.logout()

        self.assertIsNone(AuthController.current_user)
        self.assertIsNone(AuthController.get_current_role())

    def test_can_manage_users_false_for_non_admin(self):
        AuthController.current_user = {"role_name": "front_desk"}

        self.assertFalse(AuthController.can_manage_users())

    def test_can_access_feature_for_admin(self):
        self.assertTrue(AuthController.can_access_feature("user_management", "admin"))
        self.assertTrue(AuthController.can_access_feature("tenant_management", "admin"))
        self.assertTrue(AuthController.can_access_feature("apartment_management", "admin"))
        self.assertTrue(AuthController.can_access_feature("lease_management", "admin"))

    def test_can_access_feature_for_front_desk(self):
        self.assertFalse(AuthController.can_access_feature("user_management", "front_desk"))
        self.assertTrue(AuthController.can_access_feature("tenant_management", "front_desk"))
        self.assertTrue(AuthController.can_access_feature("apartment_management", "front_desk"))
        self.assertTrue(AuthController.can_access_feature("lease_management", "front_desk"))

    def test_can_access_feature_for_finance_and_maintenance(self):
        self.assertTrue(AuthController.can_access_feature("finance_dashboard", "finance"))
        self.assertFalse(AuthController.can_access_feature("finance_dashboard", "maintenance"))
        self.assertTrue(AuthController.can_access_feature("maintenance_dashboard", "maintenance"))
        self.assertFalse(AuthController.can_access_feature("maintenance_dashboard", "finance"))

    def test_can_access_feature_with_current_user_fallback(self):
        AuthController.current_user = {"role_name": "manager"}
        self.assertTrue(AuthController.can_access_feature("tenant_management"))
        self.assertTrue(AuthController.can_access_feature("finance_dashboard"))

    def test_manager_is_read_only_for_operational_actions(self):
        AuthController.current_user = {"role_name": "manager"}
        self.assertFalse(AuthController.can_perform_action("register_tenants"))
        self.assertFalse(AuthController.can_perform_action("create_leases"))
        self.assertFalse(AuthController.can_perform_action("edit_apartments"))
        self.assertFalse(AuthController.can_perform_action("process_payments"))
        self.assertFalse(AuthController.can_perform_action("log_maintenance"))

    def test_front_desk_and_finance_action_access(self):
        self.assertTrue(AuthController.can_perform_action("register_tenants", "front_desk"))
        self.assertTrue(AuthController.can_perform_action("create_leases", "front_desk"))
        self.assertTrue(AuthController.can_perform_action("process_payments", "finance"))
        self.assertFalse(AuthController.can_perform_action("edit_apartments", "front_desk"))

    def test_can_access_feature_unknown_feature_denied(self):
        self.assertFalse(AuthController.can_access_feature("unknown_feature", "admin"))


if __name__ == "__main__":
    unittest.main()
