import os
import tempfile
import unittest

from dao.user_dao import UserDAO
from database import db_manager
from utils.security import verify_password


class TestUserDAO(unittest.TestCase):
    def setUp(self):
        self._original_db_name = db_manager.DB_NAME
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # Point DAO/database code at an isolated temp DB for each test.
        db_manager.DB_NAME = self.temp_db_path
        db_manager.DBManager.initialise_database()
        UserDAO.seed_roles()

    def tearDown(self):
        db_manager.DB_NAME = self._original_db_name
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_get_roles_returns_seeded_roles(self):
        roles = UserDAO.get_roles()
        self.assertEqual(
            set(roles),
            {"admin", "front_desk", "finance", "maintenance", "manager"},
        )

    def test_create_and_get_user_by_username(self):
        UserDAO.create_user(
            full_name="Front Desk Tester",
            username="frontdesk1",
            password="secret123",
            role_name="front_desk",
            location="Bristol",
        )

        user = UserDAO.get_user_by_username("frontdesk1")
        self.assertIsNotNone(user)
        self.assertEqual(user["full_name"], "Front Desk Tester")
        self.assertEqual(user["role_name"], "front_desk")
        self.assertEqual(user["location"], "Bristol")
        self.assertEqual(user["is_active"], 1)
        self.assertTrue(verify_password("secret123", user["password_hash"]))

    def test_create_user_duplicate_username_raises_clean_error(self):
        UserDAO.create_user(
            full_name="First User",
            username="duplicate_user",
            password="secret123",
            role_name="manager",
            location="London",
        )

        with self.assertRaises(ValueError) as ctx:
            UserDAO.create_user(
                full_name="Second User",
                username="duplicate_user",
                password="secret456",
                role_name="finance",
                location="Cardiff",
            )
        self.assertEqual(str(ctx.exception), "Username already exists.")

    def test_update_user_without_password_keeps_existing_hash(self):
        UserDAO.create_user(
            full_name="Maintenance User",
            username="maint1",
            password="startpass",
            role_name="maintenance",
            location="Manchester",
        )
        before = UserDAO.get_user_by_username("maint1")

        UserDAO.update_user(
            user_id=before["id"],
            full_name="Maintenance Updated",
            username="maint1",
            role_name="maintenance",
            location="Cardiff",
            is_active=1,
            password=None,
        )
        after = UserDAO.get_user_by_username("maint1")

        self.assertEqual(after["full_name"], "Maintenance Updated")
        self.assertEqual(after["location"], "Cardiff")
        self.assertEqual(after["password_hash"], before["password_hash"])

    def test_update_user_with_password_changes_hash(self):
        UserDAO.create_user(
            full_name="Finance User",
            username="finance1",
            password="oldpass123",
            role_name="finance",
            location="London",
        )
        before = UserDAO.get_user_by_username("finance1")

        UserDAO.update_user(
            user_id=before["id"],
            full_name="Finance User",
            username="finance1",
            role_name="finance",
            location="London",
            is_active=1,
            password="newpass123",
        )
        after = UserDAO.get_user_by_username("finance1")

        self.assertNotEqual(after["password_hash"], before["password_hash"])
        self.assertTrue(verify_password("newpass123", after["password_hash"]))

    def test_deactivate_user_marks_user_inactive(self):
        UserDAO.create_user(
            full_name="Temp User",
            username="tempuser",
            password="secret123",
            role_name="front_desk",
            location="Bristol",
        )
        user = UserDAO.get_user_by_username("tempuser")

        UserDAO.deactivate_user(user["id"])
        updated = UserDAO.get_user_by_username("tempuser")

        self.assertEqual(updated["is_active"], 0)

    def test_get_all_users_contains_created_users(self):
        UserDAO.create_user(
            full_name="User One",
            username="userone",
            password="secret123",
            role_name="admin",
            location="Bristol",
        )
        UserDAO.create_user(
            full_name="User Two",
            username="usertwo",
            password="secret456",
            role_name="manager",
            location="London",
        )

        all_users = UserDAO.get_all_users()
        usernames = {row["username"] for row in all_users}
        self.assertIn("userone", usernames)
        self.assertIn("usertwo", usernames)


if __name__ == "__main__":
    unittest.main()
