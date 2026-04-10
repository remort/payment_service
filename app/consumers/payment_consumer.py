import asyncio
import json
import logging
from datetime import datetime, timedelta
from functools import partial

import aio_pika
from aio_pika import Channel, ExchangeType, IncomingMessage

from app.config import RABBITMQ_QUEUE_ARGUMENTS, settings
from app.db.models import PaymentStatus
from app.db.session import AsyncDBSession
from app.repositories.payment_repository import PaymentRepository
from app.utils.payment_emulator import emulate_payment_gateway
from app.utils.webhook import send_webhook_with_retry

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def process_payment(message: IncomingMessage, channel: Channel):
    async with message.process(ignore_processed=True):
        try:
            payload = json.loads(message.body.decode())
            payment_id = payload["payment_id"]
            webhook_url = payload["webhook_url"]
            amount = payload["amount"]
            currency = payload["currency"]

            retry_count = message.headers.get("x-retry-count", 0)
            log.info(f"Processing payment {payment_id}, retry {retry_count}")

            success = await emulate_payment_gateway(amount, currency)

            async with AsyncDBSession() as session:
                repo = PaymentRepository(session)
                status = PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
                await repo.update_status(payment_id, status, datetime.now(tz=None))
                await session.commit()

            webhook_payload = {
                "payment_id": payment_id,
                "status": status.value,
                "processed_at": datetime.now(tz=None).isoformat(),
            }
            payload_sent = await send_webhook_with_retry(webhook_url, webhook_payload)
            if not payload_sent:
                log.error("Unable to sent payment to webhook but payment succeded.")

            log.info(f"Processed payment {payment_id} with status {status.value}")

        except Exception as e:
            log.error(f"Error processing payment: {e}", exc_info=True)

            retry_count = int(str(message.headers.get("x-retry-count", 0)))
            log.info("retry_count, %s", retry_count)

            if retry_count >= settings.RABBITMQ_MESSAGE_RETRIES:
                log.error(f"Payment processing failed after 3 attempts, sending to DLQ")
                # Reject without requeue - message goes to DLX and then to DLQ
                await message.reject(requeue=False)
            else:
                log.warning(
                    f"Retry attempt {retry_count + 1}/%d for payment",
                    settings.RABBITMQ_MESSAGE_RETRIES,
                )

                new_headers = dict(message.headers)
                new_headers["x-retry-count"] = retry_count + 1

                log.info('Put message to retention queue for %s time', retry_count + 1)
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        headers=new_headers,
                        expiration=timedelta(seconds=2 ** (retry_count)),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key=settings.PAYMENTS_RETENTION,
                )


async def start_consumer():
    connection = await aio_pika.connect_robust(
        url=settings.RABBITMQ_URL,
    )
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    dlx_exchange = await channel.declare_exchange(
        settings.PAYMENTS_DLX, ExchangeType.DIRECT, durable=True
    )
    dlq = await channel.declare_queue(settings.PAYMENTS_DLQ, durable=True)
    await dlq.bind(dlx_exchange, routing_key=settings.PAYMENTS_DLQ)

    await channel.declare_queue(
        settings.PAYMENTS_RETENTION,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": settings.PAYMENTS_QUEUE,
        },
    )

    main_queue = await channel.declare_queue(
        settings.PAYMENTS_QUEUE,
        durable=True,
        arguments=RABBITMQ_QUEUE_ARGUMENTS,
    )

    await main_queue.consume(partial(process_payment, channel=channel))  # type: ignore
    log.info(
        f"Consumer started successfully, listening on queue: {settings.PAYMENTS_QUEUE}"
    )

    await asyncio.Future()
