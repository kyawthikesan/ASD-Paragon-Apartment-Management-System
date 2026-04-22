# Student Name: Kyaw Thike (oliver) San
# Student ID: 25014001
# Module: UFCF8S-30-2 Advanced Software Development
from dao.lease_dao import LeaseDAO
from datetime import datetime


class LeaseController:

    @staticmethod
    def create_lease(tenantID, apartmentID, start_date, end_date):

        # Convert to date for comparison
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except:
            return "Invalid date format (YYYY-MM-DD)"

        # Rule 1: End date > Start date
        if end <= start:
            return "End date must be after start date"

        # Rule 2: One active lease per tenant
        if LeaseDAO.has_active_lease(tenantID):
            return "Tenant already has an active lease"

        # Rule 3: Apartment must be available
        if not LeaseDAO.is_apartment_available(apartmentID):
            return "Apartment is not available"

        # Create lease
        LeaseDAO.create_lease(tenantID, apartmentID, start_date, end_date)

        # Update apartment status
        LeaseDAO.mark_apartment_occupied(apartmentID)

        return "Success"

    @staticmethod
    def get_all_leases(city=None):
        return LeaseDAO.get_all_leases(city=city)
