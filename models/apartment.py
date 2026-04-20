class Apartment:
    def __init__(self, location_id, apt_type, rent, rooms, status="available"):
        self.location_id = location_id
        self.type = apt_type
        self.rent = rent
        self.rooms = rooms
        self.status = status

    def __str__(self):
        return f"{self.type} - {self.rooms} rooms (£{self.rent})"