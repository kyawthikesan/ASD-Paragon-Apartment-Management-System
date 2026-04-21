class MaintenanceModel:
    def __init__(self, dao):
        self.dao = dao

    def validate_and_update(self, req_id, staff, date, status, cost, hours):
        if float(cost) < 0: raise ValueError("Cost cannot be negative")
        self.dao.update_maintenance(req_id, staff, date, status, cost, hours)