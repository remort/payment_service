from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_id(self, payment_id: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        payment_id: str,
        status: PaymentStatus,
        processed_at: datetime | None = None,
    ):
        await self.session.execute(
            update(Payment)
            .where(Payment.payment_id == payment_id)
            .values(status=status, processed_at=processed_at or datetime.now(tz=None))
        )
