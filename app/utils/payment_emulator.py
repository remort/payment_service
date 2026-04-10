import asyncio
import random


async def emulate_payment_gateway(amount: float, currency: str) -> bool:
    """Эмуляция внешнего шлюза: 90% успех, 10% ошибка"""
    # Симуляция задержки 2-5 секунд
    delay = random.uniform(2, 5)
    await asyncio.sleep(delay)
    
    # 90% успеха
    return random.random() < 0.9
