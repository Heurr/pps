from pendulum import Date

from app.constants import CountryCode, CurrencyCode, ProductPriceType
from app.schemas.base import BaseDBSchema, BaseIdModel


class ProductPriceHistoryBaseSchema(BaseIdModel):
    country_code: CountryCode
    currency_code: CurrencyCode
    max_price: float
    min_price: float
    avg_price: float
    price_type: ProductPriceType
    date: Date
    version: int


class ProductPriceHistoryUpdateSchema(BaseIdModel):
    country_code: CountryCode | None = None
    currency_code: CurrencyCode | None = None
    max_price: float | None = None
    min_price: float | None = None
    avg_price: float | None = None
    price_type: ProductPriceType | None = None
    date: Date
    version: int | None = None


class ProductPriceHistoryCreateSchema(ProductPriceHistoryBaseSchema):
    pass


class ProductPriceHistoryDBSchema(ProductPriceHistoryBaseSchema, BaseDBSchema):
    pass
