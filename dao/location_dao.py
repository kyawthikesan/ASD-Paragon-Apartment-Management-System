from database.db_manager import connect

def add_location(city):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO locations (city)
    VALUES (?)
    """, (city,))

    conn.commit()
    conn.close()