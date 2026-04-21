from dao.maintenance_dao import MaintenanceDAO


class MaintenanceController:
    VALID_PRIORITIES = {"Low", "Medium", "High", "Urgent"}
    VALID_STATUSES = {"Open", "In Progress", "Resolved"}

    @staticmethod
    def create_request(apartmentID, tenantID, title, description, priority="Medium"):
        if not title or not title.strip():
            return "Request title is required."

        if priority not in MaintenanceController.VALID_PRIORITIES:
            return "Invalid priority."

        MaintenanceDAO.add_request(
            apartmentID=apartmentID,
            tenantID=tenantID,
            title=title.strip(),
            description=(description or "").strip(),
            priority=priority,
            status="Open",
        )
        return "Success"

    @staticmethod
    def get_all_requests(city=None):
        return MaintenanceDAO.get_all_requests(city=city)

    @staticmethod
    def update_request_status(request_id, status):
        if status not in MaintenanceController.VALID_STATUSES:
            return "Invalid status."
        MaintenanceDAO.update_request_status(request_id, status)
        return "Success"
