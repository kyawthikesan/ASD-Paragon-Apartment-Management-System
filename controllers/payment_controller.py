from datetime import datetime
from dao.payment_dao import PaymentDAO


class PaymentController:
    VALID_STATUSES = {"Pending", "Paid", "Overdue"}

    @staticmethod
    def create_payment(tenantID, apartmentID, amount_text, payment_date, method, status="Pending", note=None):
        try:
            amount = float(amount_text)
        except (TypeError, ValueError):
            return "Amount must be a valid number."

        if amount <= 0:
            return "Amount must be greater than 0."

        if not method:
            return "Payment method is required."

        try:
            datetime.strptime(payment_date, "%Y-%m-%d")
        except ValueError:
            return "Payment date must be in YYYY-MM-DD format."

        if status not in PaymentController.VALID_STATUSES:
            return "Invalid payment status."

        PaymentDAO.add_payment(
            tenantID=tenantID,
            apartmentID=apartmentID,
            amount=amount,
            payment_date=payment_date,
            method=method,
            status=status,
            note=note,
        )
        return "Success"

    @staticmethod
    def get_all_payments(city=None):
        return PaymentDAO.get_all_payments(city=city)

    @staticmethod
    def update_payment_status(payment_id, status):
        if status not in PaymentController.VALID_STATUSES:
            return "Invalid payment status."
        PaymentDAO.update_payment_status(payment_id, status)
        return "Success"
