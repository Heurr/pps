from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Generic
from uuid import UUID

from app.constants import CountryCode, CurrencyCode, ProductPriceType
from app.crud.base import CreateSchemaTypeT, DBSchemaTypeT
from app.schemas.base import BaseModel


class PriceEventAction(StrEnum):
    UPSERT = "upsert"
    DELETE = "delete"


@dataclass
class EntityUpdate(Generic[DBSchemaTypeT, CreateSchemaTypeT]):
    old: DBSchemaTypeT | None
    new: CreateSchemaTypeT | None


class PriceChange(BaseModel):
    min_price: float
    max_price: float


class PriceEvent(BaseModel):
    product_id: UUID
    type: ProductPriceType
    action: PriceEventAction
    price: float
    old_price: float | None
    country_code: CountryCode
    currency_code: CurrencyCode
    created_at: datetime
