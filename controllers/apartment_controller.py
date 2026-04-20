from dao.apartment_dao import ApartmentDAO


class ApartmentController:

    @staticmethod
    def add_apartment(locationID, type, rent, rooms):
        ApartmentDAO.add_apartment(locationID, type, rent, rooms)

    @staticmethod
    def get_all_apartments():
        return ApartmentDAO.get_all_apartments()

    @staticmethod
    def update_apartment(apartmentID, locationID, type, rent, rooms):
        ApartmentDAO.update_apartment(apartmentID, locationID, type, rent, rooms)

    @staticmethod
    def delete_apartment(apartmentID):
        ApartmentDAO.delete_apartment(apartmentID)

    @staticmethod
    def search_apartment(keyword):
        return ApartmentDAO.search_apartment(keyword)