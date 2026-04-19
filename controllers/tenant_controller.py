from dao.tenant_dao import TenantDAO

class TenantController:

    @staticmethod
    def add_tenant(name, NI_number, phone, email):
        NI_number = NI_number.upper()
        TenantDAO.add_tenant(name, NI_number, phone, email)

    @staticmethod
    def get_all_tenants():
        return TenantDAO.get_all_tenants()

    @staticmethod
    def update_tenant(tenant_id, name, NI_number, phone, email):
        NI_number = NI_number.upper()
        TenantDAO.update_tenant(tenant_id, name, NI_number, phone, email)

    @staticmethod
    def delete_tenant(tenant_id):
        TenantDAO.delete_tenant(tenant_id)