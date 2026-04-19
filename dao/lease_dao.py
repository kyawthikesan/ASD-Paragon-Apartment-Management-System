from database.db_manager import connect
from datetime import datetime
from dao.apartment_dao import is_apartment_available, assign_apartment

def create_lease(tenant_id, apartment_id, start_date, end_date):
    conn = connect()
    cursor = conn.cursor()

    # 🔥 RULE 1: check apartment availability
    if not is_apartment_available(apartment_id):
        print("Apartment is already occupied")
        return

    # 🔥 RULE 2: validate dates
    if datetime.strptime(end_date, "%Y-%m-%d") <= datetime.strptime(start_date, "%Y-%m-%d"):
        print("Invalid lease dates")
        return

    # 🔥 RULE 3: one active lease per tenant
    cursor.execute("""
    SELECT * FROM leases
    WHERE tenantID = ? AND status = 'active'
    """, (tenant_id,))

    if cursor.fetchone():
        print("Tenant already has an active lease")
        return

    # ✅ create lease
    cursor.execute("""
    INSERT INTO leases (tenantID, apartmentID, startDate, endDate, status)
    VALUES (?, ?, ?, ?, 'active')
    """, (tenant_id, apartment_id, start_date, end_date))

    # 🔥 update apartment status
    assign_apartment(apartment_id)

    conn.commit()
    conn.close()

    print("Lease created successfully")

def terminate_lease(lease_id):
    conn = connect()
    cursor = conn.cursor()

    # get lease details
    cursor.execute("""
    SELECT apartmentID FROM leases WHERE leaseID = ?
    """, (lease_id,))
    
    apartment_id = cursor.fetchone()[0]

    # set lease inactive
    cursor.execute("""
    UPDATE leases
    SET status = 'terminated'
    WHERE leaseID = ?
    """, (lease_id,))

    # free apartment
    cursor.execute("""
    UPDATE apartments
    SET status = 'available'
    WHERE apartmentID = ?
    """, (apartment_id,))

    conn.commit()
    conn.close()