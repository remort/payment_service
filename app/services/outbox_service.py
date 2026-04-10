import asyncio
import json
import logging
import ssl

import aio_pika
import certifi

from app.config import RABBITMQ_QUEUE_ARGUMENTS, settings
from app.db.session import AsyncDBSession
from app.repositories.outbox_repository import OutboxRepository

log = logging.getLogger(__name__)


class OutboxProcessor:
    async def start(self):
        context = ssl.create_default_context(cafile=certifi.where())
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        self.connection = await aio_pika.connect_robust(
            url=settings.RABBITMQ_URL,
            ssl_context=context,
        )
        self.channel = await self.connection.channel()
        await self.channel.declare_queue(
            settings.PAYMENTS_QUEUE,
            durable=True,
            arguments=RABBITMQ_QUEUE_ARGUMENTS,
        )

        while True:
            try:
                await self.process_outbox()
            except Exception as e:
                log.error(f"Outbox processor error: {e}")
            await asyncio.sleep(settings.OUTBOX_POLL_INTERVAL_SECONDS)

    async def process_outbox(self):
        async with AsyncDBSession() as session:
            repo = OutboxRepository(session)
            events = await repo.get_unprocessed(limit=10)

            for event in events:
                try:
                    await self.channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(event.payload).encode(),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key=settings.PAYMENTS_QUEUE,
                    )
                    await repo.mark_processed(event.id)
                    await session.commit()
                    log.info(f"Published outbox event {event.event_id}")
                except Exception as e:
                    log.error(f"Failed to publish event {event.event_id}: {e}")
                    await repo.increment_retry(event.id)
                    await session.commit()
