import os
import tempfile
import unittest

from controllers.maintenance_controller import MaintenanceController
from controllers.payment_controller import PaymentController
from dao.apartment_dao import ApartmentDAO
from dao.invoice_dao import InvoiceDAO
from dao.lease_dao import LeaseDAO
from dao.location_dao import LocationDAO
from dao.payment_dao import PaymentDAO
from dao.tenant_dao import TenantDAO
from database import db_manager


class TestPaymentAndMaintenance(unittest.TestCase):
    def setUp(self):
        self._original_db_name = db_manager.DB_NAME
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        db_manager.DB_NAME = self.temp_db_path
        db_manager.DBManager.initialise_database()

        location_id = LocationDAO.add_location("Bristol")
        ApartmentDAO.add_apartment(location_id, "1-bedroom", 1000, 1)
        TenantDAO.add_tenant("Flow User", "NI999999A", "07000000000", "flow@example.com")

        self.apartment_id = ApartmentDAO.get_all_apartments()[0]["apartmentID"]
        self.tenant_id = TenantDAO.get_all_tenants()[0]["tenantID"]

        # Current finance flow is:
        # tenant + apartment -> lease -> invoice -> payment
        LeaseDAO.create_lease(
            tenantID=self.tenant_id,
            apartmentID=self.apartment_id,
            start_date="2026-04-01",
            end_date="2027-03-31",
        )

        self.lease_id = LeaseDAO.get_all_leases()[0]["leaseID"]

        self.invoice_id = InvoiceDAO.create_invoice(
            leaseID=self.lease_id,
            billing_period_start="2026-04-01",
            billing_period_end="2026-04-30",
            due_date="2026-04-30",
            amount_due=1250.50,
            status="UNPAID",
        )

    def tearDown(self):
        db_manager.DB_NAME = self._original_db_name
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_create_payment_and_update_status(self):
        # Updated to match the current invoice-based schema
        payment_id = PaymentDAO.create_payment(
            invoiceID=self.invoice_id,
            payment_date="2026-04-20",
            amount_paid=1250.50,
            payment_method="CARD",
        )
        self.assertIsInstance(payment_id, int)

        rows = PaymentDAO.get_all_payments()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["invoiceID"], self.invoice_id)
        self.assertEqual(float(rows[0]["amount_paid"]), 1250.50)

        invoice = InvoiceDAO.get_invoice_by_id(self.invoice_id)
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice["status"], "PAID")

    def test_create_payment_validation(self):
        self.assertEqual(
            PaymentController.create_payment(
                tenantID=self.tenant_id,
                apartmentID=self.apartment_id,
                amount_text="-1",
                payment_date="2026-04-20",
                method="Card",
            ),
            "Amount must be greater than 0.",
        )
        self.assertEqual(
            PaymentController.create_payment(
                tenantID=self.tenant_id,
                apartmentID=self.apartment_id,
                amount_text="100",
                payment_date="20-04-2026",
                method="Card",
            ),
            "Payment date must be in YYYY-MM-DD format.",
        )

    def test_create_request_and_update_status(self):
        result = MaintenanceController.create_request(
            apartmentID=self.apartment_id,
            tenantID=self.tenant_id,
            title="Leaking sink",
            description="Water leaking under sink in kitchen.",
            priority="High",
        )
        self.assertEqual(result, "Success")

        rows = MaintenanceController.get_all_requests()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "Open")

        update_result = MaintenanceController.update_request_status(rows[0]["requestID"], "In Progress")
        self.assertEqual(update_result, "Success")
        self.assertEqual(MaintenanceController.get_all_requests()[0]["status"], "In Progress")

    def test_create_request_validation(self):
        self.assertEqual(
            MaintenanceController.create_request(
                apartmentID=self.apartment_id,
                tenantID=self.tenant_id,
                title="",
                description="Missing title",
                priority="High",
            ),
            "Request title is required.",
        )
        self.assertEqual(
            MaintenanceController.create_request(
                apartmentID=self.apartment_id,
                tenantID=self.tenant_id,
                title="Broken lock",
                description="Door lock is stuck.",
                priority="Impossible",
            ),
            "Invalid priority.",
        )


if __name__ == "__main__":
    unittest.main()