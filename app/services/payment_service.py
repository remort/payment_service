import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OutboxEvent, Payment, PaymentStatus
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas import PaymentCreate


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.payment_repo = PaymentRepository(session)
        self.outbox_repo = OutboxRepository(session)

    async def create_payment(
        self, create_data: PaymentCreate, idempotency_key: str
    ) -> Payment:
        existing = await self.payment_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        payment_id = str(uuid.uuid4())
        payment = Payment(
            payment_id=payment_id,
            amount=create_data.amount,  # Decimal уже правильный тип
            currency=create_data.currency,
            description=create_data.description,
            payment_metadata=create_data.payment_metadata,
            idempotency_key=idempotency_key,
            webhook_url=str(create_data.webhook_url),
            status=PaymentStatus.PENDING,
        )

        await self.payment_repo.create(payment)

        # Создаем outbox событие
        outbox_event = OutboxEvent(
            event_id=str(uuid.uuid4()),
            aggregate_id=payment_id,
            event_type="payment.created",
            payload={
                "payment_id": payment_id,
                "amount": float(payment.amount),  # конвертируем для JSON
                "currency": payment.currency,
                "webhook_url": payment.webhook_url,
            },
        )
        await self.outbox_repo.save(outbox_event)

        return payment

    async def get_payment(self, payment_id: str) -> Payment | None:
        return await self.payment_repo.get_by_id(payment_id)
