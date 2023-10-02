from uuid import UUID

from pydantic import Field

from app.constants import CountryCode, CurrencyCode, PriceType
from app.schemas.base import BaseMessageModel, BaseModel


class Price(BaseModel):
    type: PriceType
    amount: float
    currency_code: CurrencyCode
    vat: float


class OfferMessageSchema(BaseMessageModel):
    local_product_id: str
    product_id: UUID | None  # Compute using UUIDv5 from local id
    country_code: CountryCode
    shop_id: UUID = Field(..., alias="shopId")
    prices: list[Price]
