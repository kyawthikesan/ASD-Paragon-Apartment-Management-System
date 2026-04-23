import unittest
import sqlite3
from maintenance_dao import MaintenanceDAO

class TestMaintenanceModule(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database so we don't mess up your real system.db
        self.dao = MaintenanceDAO(":memory:")

    def test_log_request(self):
        """Test if a request can be logged."""
        self.dao.log_request(999)
        rows = self.dao.get_all_requests()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], 999)

    def test_update_valid_data(self):
        """Test updating a record with valid information."""
        self.dao.log_request(101)
        self.dao.update_maintenance(1, "Test Staff", "2026-04-21", "Resolved", 50.0, 2)
        row = self.dao.get_all_requests()[0]
        self.assertEqual(row[2], "Test Staff")
        self.assertEqual(row[4], "Resolved")
        self.assertEqual(row[5], 50.0)

    def test_database_integrity(self):
        """Ensure IDs increment correctly."""
        self.dao.log_request(101)
        self.dao.log_request(102)
        rows = self.dao.get_all_requests()
        self.assertEqual(rows[0][0], 1)
        self.assertEqual(rows[1][0], 2)

if __name__ == "__main__":
    unittest.main()