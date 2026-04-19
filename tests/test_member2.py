from dao.apartment_dao import add_apartment
from dao.location_dao import add_location
from dao.lease_dao import create_lease

add_location("London")
add_apartment(1, "2-bedroom", 1200, 2)

create_lease(1, 1, "2026-01-01", "2026-12-01")