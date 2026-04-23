import unittest
from unittest.mock import patch

from controllers.auth_controller import AuthController
from main import PAMSApp


class DummyApp:
    def __init__(self):
        self.called = None

    def show_admin_dashboard(self):
        self.called = "admin"

    def show_front_desk_dashboard(self):
        self.called = "front_desk"

    def show_finance_dashboard(self):
        self.called = "finance"

    def show_maintenance_dashboard(self):
        self.called = "maintenance"

    def show_manager_dashboard(self):
        self.called = "manager"

    def logout(self):
        self.called = "logout"

    def route_dashboard_by_role(self, role=None):
        self.called = f"route:{role}"

    def _show_access_denied_modal(self, feature_name):
        self.called = f"denied:{feature_name}"


class TestNavigationIntegration(unittest.TestCase):
    def setUp(self):
        AuthController.logout()

    def tearDown(self):
        AuthController.logout()

    def test_route_dashboard_by_role_direct_mapping(self):
        app = DummyApp()

        PAMSApp.route_dashboard_by_role(app, "admin")
        self.assertEqual(app.called, "admin")

        PAMSApp.route_dashboard_by_role(app, "front_desk")
        self.assertEqual(app.called, "front_desk")

        PAMSApp.route_dashboard_by_role(app, "finance")
        self.assertEqual(app.called, "finance")

        PAMSApp.route_dashboard_by_role(app, "maintenance")
        self.assertEqual(app.called, "maintenance")

        PAMSApp.route_dashboard_by_role(app, "manager")
        self.assertEqual(app.called, "manager")

    def test_route_dashboard_by_role_fallback_to_logout(self):
        app = DummyApp()
        PAMSApp.route_dashboard_by_role(app, "unknown")
        self.assertEqual(app.called, "logout")

    @patch("controllers.auth_controller.AuthController.refresh_current_user")
    def test_route_dashboard_by_role_reads_current_user_role(self, mock_refresh):
        app = DummyApp()
        AuthController.current_user = {"role_name": "manager"}
        PAMSApp.route_dashboard_by_role(app)
        self.assertEqual(app.called, "manager")

    def test_require_feature_access_denies_and_routes_back(self):
        app = DummyApp()
        AuthController.current_user = {"role_name": "finance"}

        allowed = PAMSApp._require_feature_access(app, "tenant_management", "Tenant Management")

        self.assertFalse(allowed)
        self.assertEqual(app.called, "denied:Tenant Management")

    def test_require_feature_access_allows(self):
        app = DummyApp()
        AuthController.current_user = {"role_name": "admin"}

        allowed = PAMSApp._require_feature_access(app, "user_management", "User Management")

        self.assertTrue(allowed)
        self.assertIsNone(app.called)


if __name__ == "__main__":
    unittest.main()