class ComplaintModel:
    def __init__(self, dao):
        self.dao = dao

    def create_complaint(self, description):
        with self.dao.conn:
            self.dao.conn.execute("INSERT INTO complaints (description) VALUES (?)", (description,))