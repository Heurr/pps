from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.constants import CountryCode, CurrencyCode, PriceType
from app.schemas.base import BaseDBSchema, BaseModel, EntityModel, MessageModel


class OfferPrice(BaseModel):
    type: PriceType
    amount: float
    currency_code: CurrencyCode = Field(alias="currencyCode")


class OfferLegacy(BaseModel):
    country_code: CountryCode = Field(alias="countryCode")


class OfferMessageSchema(MessageModel):
    """
    Docs: https://ofp.gpages.heu.group/offer-api/
    """

    id: UUID
    product_id: UUID | None = Field(alias="productId")
    shop_id: UUID = Field(alias="shopId")
    legacy: OfferLegacy
    prices: list[OfferPrice]

    @field_validator("product_id", mode="before")
    @classmethod
    def empty_product_id(cls, value):
        return None if value == "" else value


class OfferCreateSchema(EntityModel):
    product_id: UUID
    shop_id: UUID
    price: float
    currency_code: CurrencyCode
    in_stock: bool | None = None
    buyable: bool | None = None
    availability_version: int = -1
    buyable_version: int = -1


class PopulationOfferSchema(BaseModel):
    id: UUID
    product_id: UUID
    created_at: datetime
    in_stock: bool | None = None
    buyable: bool | None = None
    availability_version: int | None = None
    buyable_version: int | None = None


class OfferDBSchema(OfferCreateSchema, BaseDBSchema):
    certified_shop: bool | None = None
