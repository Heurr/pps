from uuid import UUID

from app.constants import CurrencyCode, PriceType
from app.schemas.base import BaseDBSchema, BaseModel, EntityModel


class Price(BaseModel):
    type: PriceType
    amount: float
    currency_code: CurrencyCode
    vat: float  # is it needed?


class OfferMessageSchema(EntityModel):
    local_product_id: str  # is it needed?
    product_id: UUID | None  # when can product id be none?
    shop_id: UUID
    prices: list[Price]  # why list?
    # Add more attributes when working on workers


class OfferCreateSchema(EntityModel):
    product_id: UUID
    shop_id: UUID
    price: float
    currency_code: CurrencyCode


class OfferDBSchema(OfferCreateSchema, BaseDBSchema):
    pass
