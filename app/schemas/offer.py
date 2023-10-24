from uuid import UUID

from pydantic import Field

from app.constants import CountryCode, CurrencyCode, PriceType
from app.schemas.base import BaseDBSchema, BaseIdModel, BaseMessageModel, BaseModel


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


class OfferBaseSchema(BaseIdModel):
    product_id: UUID
    country_code: CountryCode
    shop_id: UUID
    amount: float
    currency_code: CurrencyCode
    version: int


class OfferUpdateSchema(BaseIdModel):
    product_id: UUID
    country_code: CountryCode | None = None
    shop_id: UUID | None = None
    amount: float | None = None
    currency_code: CurrencyCode | None = None
    version: int | None = None


class OfferCreateSchema(OfferBaseSchema):
    pass


class OfferDBSchema(OfferBaseSchema, BaseDBSchema):
    pass
