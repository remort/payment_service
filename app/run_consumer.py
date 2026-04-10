#!/usr/bin/env python
import asyncio
import logging
import signal
import sys

from app.consumers.payment_consumer import start_consumer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def main():
    task = asyncio.create_task(start_consumer())
    
    def shutdown():
        log.info("Shutting down consumer...")
        task.cancel()
    
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown)
    
    try:
        await task
    except asyncio.CancelledError:
        log.info("Consumer stopped")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
