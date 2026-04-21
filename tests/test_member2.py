import os
import tempfile
import unittest

from dao.apartment_dao import ApartmentDAO
from dao.lease_dao import LeaseDAO
from dao.location_dao import LocationDAO
from dao.tenant_dao import TenantDAO
from database import db_manager


class TestMember2Flow(unittest.TestCase):
    def setUp(self):
        self._original_db_name = db_manager.DB_NAME
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # Use a fresh temporary DB so this suite is deterministic.
        db_manager.DB_NAME = self.temp_db_path
        db_manager.DBManager.initialise_database()

    def tearDown(self):
        db_manager.DB_NAME = self._original_db_name
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_can_create_location_apartment_tenant_and_lease(self):
        location_id = LocationDAO.add_location("London")
        ApartmentDAO.add_apartment(location_id, "2-bedroom", 1200, 2)
        TenantDAO.add_tenant("Test Tenant", "NI123456A", "07123456789", "tenant@example.com")

        apartments = ApartmentDAO.get_all_apartments()
        self.assertEqual(len(apartments), 1)
        apartment_id = apartments[0]["apartmentID"]

        tenants = TenantDAO.get_all_tenants()
        self.assertEqual(len(tenants), 1)
        tenant_id = tenants[0]["tenantID"]

        LeaseDAO.create_lease(tenant_id, apartment_id, "2026-01-01", "2026-12-01")
        leases = LeaseDAO.get_all_leases()
        self.assertEqual(len(leases), 1)
        self.assertEqual(leases[0]["status"], "Active")

    def test_mark_apartment_occupied_updates_availability(self):
        location_id = LocationDAO.add_location("Cardiff")
        ApartmentDAO.add_apartment(location_id, "Studio", 900, 1)
        apartment_id = ApartmentDAO.get_all_apartments()[0]["apartmentID"]

        self.assertTrue(LeaseDAO.is_apartment_available(apartment_id))
        LeaseDAO.mark_apartment_occupied(apartment_id)
        self.assertFalse(LeaseDAO.is_apartment_available(apartment_id))


if __name__ == "__main__":
    unittest.main()
