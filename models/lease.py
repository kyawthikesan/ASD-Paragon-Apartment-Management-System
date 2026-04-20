class Lease:
    def __init__(self, tenant_id, apartment_id, start_date, end_date, status="active"):
        self.tenant_id = tenant_id
        self.apartment_id = apartment_id
        self.start_date = start_date
        self.end_date = end_date
        self.status = status

    def __str__(self):
        return f"Lease: Tenant {self.tenant_id} → Apartment {self.apartment_id}"