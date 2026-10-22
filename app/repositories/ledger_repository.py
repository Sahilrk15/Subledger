from typing import List, Optional

from sqlalchemy import select

from app.models.ledger_entry import LedgerEntry


class LedgerRepository:
    """Deliberately exposes only ``add`` and read methods: there is no update or delete,
    which (together with the model-level guard) keeps the ledger append-only."""

    def __init__(self, db):
        self.db = db

    def add(self, entry: LedgerEntry) -> LedgerEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_by_customer(
        self,
        customer_id: int,
        entry_type: Optional[str] = None,
        invoice_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LedgerEntry]:
        stmt = select(LedgerEntry).where(LedgerEntry.customer_id == customer_id).order_by(LedgerEntry.id)
        if entry_type:
            stmt = stmt.where(LedgerEntry.entry_type == entry_type)
        if invoice_id is not None:
            stmt = stmt.where(LedgerEntry.invoice_id == invoice_id)
        return list(self.db.scalars(stmt.offset(skip).limit(limit)))

    def list_by_reference(self, reference_id: str) -> List[LedgerEntry]:
        stmt = select(LedgerEntry).where(LedgerEntry.reference_id == reference_id).order_by(LedgerEntry.id)
        return list(self.db.scalars(stmt))
