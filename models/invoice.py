from dataclasses import dataclass


@dataclass
class Invoice:
    invoiceID: int | None
    leaseID: int
    billing_period_start: str
    billing_period_end: str
    due_date: str
    amount_due: float
    status: str = "UNPAID"
    created_at: str | None = None