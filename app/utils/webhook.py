import asyncio
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


async def send_webhook_with_retry(
    url: str,
    payload: dict[str, Any],
    max_retries: int = 3,
) -> bool:
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=1.0, verify=False) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                log.info(f"Webhook sent to {url}, attempt {attempt + 1}")
                return True
        except Exception as e:
            log.error(f"Webhook attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                delay = 2**attempt
                await asyncio.sleep(delay)
            else:
                log.error(f"Webhook failed after {max_retries} attempts for {url}")
                return False
    return False
