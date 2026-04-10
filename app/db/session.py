import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar, cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings

log = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncDBSession = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

P = ParamSpec('P')
R = TypeVar('R')


def managed_db_session(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        db_session: AsyncSession = cast(AsyncSession, kwargs.get('db_session'))
        try:
            async with db_session.begin():
                result = await func(*args, **kwargs)
            log.info('Got successful result. Commit DB changes.: %s', result)
            await db_session.commit()
            return result
        except Exception as exc:
            log.warning('Exception caught: %s.', exc)
            if db_session.dirty or db_session.new or db_session.deleted:
                log.warning(
                    'DB session is dirty '
                    '(Dirty: %s, New objects: %s, Deleted objects: %s) - do rollback.',
                    db_session.dirty,
                    db_session.new,
                    db_session.deleted,
                )
                await db_session.rollback()
            else:
                log.info('DB session is not dirty - no need to roll it back.')
            raise

    return wrapper


class DBSessionMiddleware:
    def __init__(self, app: ASGIApp, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] == 'http':
            scope['db_session'] = self.session_factory()
            try:
                await self.app(scope, receive, send)
            finally:
                db_session = scope.pop('db_session', None)
                if db_session is not None:
                    await db_session.close()
            return
        await self.app(scope, receive, send)
