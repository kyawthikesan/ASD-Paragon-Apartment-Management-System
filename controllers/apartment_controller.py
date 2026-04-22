# Student Name: Nang Phwe Hleng Hun
# Student ID: 24043841
# Module: UFCF8S-30-2 Advanced Software Development

from dao.apartment_dao import ApartmentDAO


class ApartmentController:

    @staticmethod
    def add_apartment(locationID, type, rent, rooms):
        ApartmentDAO.add_apartment(locationID, type, rent, rooms)

    @staticmethod
    def get_all_apartments(city=None):
        return ApartmentDAO.get_all_apartments(city=city)

    @staticmethod
    def update_apartment(apartmentID, locationID, type, rent, rooms):
        ApartmentDAO.update_apartment(apartmentID, locationID, type, rent, rooms)

    @staticmethod
    def delete_apartment(apartmentID):
        ApartmentDAO.delete_apartment(apartmentID)

    @staticmethod
    def search_apartment(keyword, city=None):
        return ApartmentDAO.search_apartment(keyword, city=city)
