# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

class ComplaintModel:
    def __init__(self, dao):
        self.dao = dao

    def create_complaint(self, description):
        with self.dao.conn:
            self.dao.conn.execute("INSERT INTO complaints (description) VALUES (?)", (description,))