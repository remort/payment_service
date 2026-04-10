from datetime import datetime
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OutboxEvent


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event: OutboxEvent):
        self.session.add(event)
        await self.session.flush()

    async def get_unprocessed(self, limit: int = 100) -> Sequence[OutboxEvent]:
        result = await self.session.execute(
            select(OutboxEvent).where(OutboxEvent.processed_at.is_(None)).limit(limit)
        )
        return result.scalars().all()

    async def mark_processed(self, event_id: int):
        await self.session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed_at=datetime.now(tz=None))
        )

    async def increment_retry(self, event_id: int):
        await self.session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1)
        )
