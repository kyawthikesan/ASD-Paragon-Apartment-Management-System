class Tenant:
    def __init__(self, name, phone, email, NI_number):
        self.name = name
        self.phone = phone
        self.email = email
        self.NI_number = NI_number

    def __str__(self):
        return f"{self.name} ({self.NI_number})"