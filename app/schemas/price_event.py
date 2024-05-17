from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.constants import CountryCode, CurrencyCode, ProductPriceType
from app.schemas.base import BaseModel


class PriceEventAction(StrEnum):
    UPSERT = "upsert"
    DELETE = "delete"


class PriceChange(BaseModel):
    min_price: float
    max_price: float


class PriceEvent(BaseModel):
    product_id: UUID
    type: ProductPriceType
    action: PriceEventAction
    price: float | None = None
    old_price: float | None = None
    country_code: CountryCode
    currency_code: CurrencyCode
    created_at: datetime
