from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(..., pattern="^(RUB|USD|EUR)$")
    description: str = Field(..., max_length=255)
    payment_metadata: dict[str, Any] | None = None
    webhook_url: HttpUrl

class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    payment_id: str
    status: str
    created_at: datetime

class PaymentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    payment_id: str
    status: str
    created_at: datetime
    amount: Decimal
    currency: str
    description: str
    payment_metadata: dict[str, Any] | None
    webhook_url: str
    processed_at: datetime | None
