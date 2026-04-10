import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from starlette.middleware import Middleware

from app.api.v1 import payments
from app.db.session import AsyncDBSession, Base, DBSessionMiddleware, engine
from app.services.outbox_service import OutboxProcessor

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    outbox = OutboxProcessor()
    outbox_task = asyncio.create_task(outbox.start())
    
    log.info("Application started successfully")    

    yield

    log.info("Shutting down...")
    outbox_task.cancel()
    with suppress(asyncio.CancelledError):
        await asyncio.wait_for(outbox_task, 1)

    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    middleware=[
        Middleware(
            DBSessionMiddleware,
            session_factory=AsyncDBSession,   
        )
    ],
)
app.include_router(payments.router)
