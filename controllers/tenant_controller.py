# Student Name: Kyaw Thike (oliver) San
# Student ID: 25014001
# Module: UFCF8S-30-2 Advanced Software Development

from dao.tenant_dao import TenantDAO

class TenantController:

    @staticmethod
    def add_tenant(name, NI_number, phone, email):
        NI_number = NI_number.upper()
        TenantDAO.add_tenant(name, NI_number, phone, email)

    @staticmethod
    def get_all_tenants(city=None):
        return TenantDAO.get_all_tenants(city=city)

    @staticmethod
    def update_tenant(tenant_id, name, NI_number, phone, email):
        NI_number = NI_number.upper()
        TenantDAO.update_tenant(tenant_id, name, NI_number, phone, email)

    @staticmethod
    def delete_tenant(tenant_id):
        TenantDAO.delete_tenant(tenant_id)
