from uuid import UUID

from app.constants import CurrencyCode, PriceType
from app.schemas.base import BaseDBSchema, BaseModel, EntityModel


class Price(BaseModel):
    type: PriceType
    amount: float
    currency_code: CurrencyCode
    vat: float


class OfferMessageSchema(EntityModel):
    local_product_id: str
    product_id: UUID | None
    shop_id: UUID
    prices: list[Price]
    # Add more attributes when working on workers


class OfferCreateSchema(EntityModel):
    product_id: UUID
    shop_id: UUID
    amount: float
    currency_code: CurrencyCode


class OfferUpdateSchema(EntityModel):
    product_id: UUID
    shop_id: UUID | None = None
    amount: float | None = None
    currency_code: CurrencyCode | None = None


class OfferDBSchema(OfferCreateSchema, BaseDBSchema):
    pass
