import datetime as dt
from uuid import UUID

from pydantic import ConfigDict, Field

from app.constants import Action, CountryCode, CurrencyCode, ProductPriceType
from app.schemas.base import BaseModel


class ProductPriceCreateSchema(BaseModel):
    day: dt.date
    product_id: UUID
    country_code: CountryCode
    price_type: ProductPriceType
    min_price: float
    max_price: float
    currency_code: CurrencyCode
    updated_at: dt.datetime


class ProductPriceDBSchema(ProductPriceCreateSchema):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ProductPricePricesDropRabbitSchema(BaseModel):
    percentage: int
    baseline_price: float
    shop_count: int


class ProductPricePricesRabbitSchema(BaseModel):
    min: float
    max: float
    price_drop: ProductPricePricesDropRabbitSchema | None = None
    type: ProductPriceType


class ProductPriceRabbitSchema(BaseModel):
    product_id: UUID = Field(alias="productId")
    currency_code: CurrencyCode = Field(alias="currencyCode")
    country_code: CountryCode = Field(alias="countryCode")
    prices: list[ProductPricePricesRabbitSchema]
    version: int
    action: Action
