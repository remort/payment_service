from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import managed_db_session
from app.dependencies import (
    db_session_dependency,
    get_idempotency_key,
    get_payment_service,
    verify_api_key,
)
from app.schemas import PaymentCreate, PaymentDetailResponse, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(
    prefix="/api/v1", dependencies=[Depends(verify_api_key)], tags=["Payments API"]
)


@router.post(
    "/payments", status_code=HTTPStatus.ACCEPTED, response_model=PaymentResponse
)
@managed_db_session
async def create_payment(
    payment_data: PaymentCreate,
    idempotency_key: str = Depends(get_idempotency_key),
    db_session: AsyncSession = Depends(db_session_dependency),
    payment_service: PaymentService = Depends(get_payment_service),
):
    payment = await payment_service.create_payment(payment_data, idempotency_key)

    print('return')
    return PaymentResponse.model_validate(payment)


@router.get("/payments/{payment_id}", response_model=PaymentDetailResponse)
@managed_db_session
async def get_payment(
    payment_id: str,
    db_session: AsyncSession = Depends(db_session_dependency),
    payment_service: PaymentService = Depends(get_payment_service),
):
    payment = await payment_service.get_payment(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return PaymentDetailResponse.model_validate(payment)
