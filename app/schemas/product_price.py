import datetime as dt
from uuid import UUID

from pydantic import ConfigDict

from app.constants import CountryCode, CurrencyCode, ProductPriceType
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
