from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.payment_service import PaymentService

api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(api_key: str = Depends(api_key_header)) -> bool:
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid API Key"
        )
    return True


def get_idempotency_key(
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
):
    if not idempotency_key:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Idempotency-Key header required",
        )
    return idempotency_key


def db_session_dependency(request: Request) -> AsyncSession:
    session: AsyncSession = request.scope['db_session']
    return session


def get_payment_service(
    db_session: AsyncSession = Depends(db_session_dependency),
) -> PaymentService:
    return PaymentService(db_session)
