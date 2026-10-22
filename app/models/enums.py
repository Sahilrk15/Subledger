"""String enums shared by models and schemas. Values are stored as plain strings in the DB."""
from enum import Enum


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class PlanStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CANCELLED = "cancelled"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class PaymentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class LedgerEntryType(str, Enum):
    INVOICE_CREATED = "invoice_created"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILURE = "payment_failure"


def enum_value(value):
    """Return the plain string for an Enum member (or the value itself if already a string)."""
    return value.value if isinstance(value, Enum) else value
