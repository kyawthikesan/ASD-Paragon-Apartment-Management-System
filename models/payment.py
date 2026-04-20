from dataclasses import dataclass


@dataclass
class Payment:
    paymentID: int | None
    invoiceID: int
    payment_date: str
    amount_paid: float
    payment_method: str = "MANUAL"
    receipt_number: str | None = None
    created_at: str | None = None