from pendulum import Date

from app.constants import CurrencyCode, ProductPriceType
from app.schemas.base import BaseDBSchema, BaseIdCountryModel


class ProductPriceHistoryBaseSchema(BaseIdCountryModel):
    date: Date
    currency_code: CurrencyCode
    max_price: float
    min_price: float
    avg_price: float
    price_type: ProductPriceType
    version: int


class ProductPriceHistoryUpdateSchema(BaseIdCountryModel):
    date: Date
    currency_code: CurrencyCode | None = None
    max_price: float | None = None
    min_price: float | None = None
    avg_price: float | None = None
    price_type: ProductPriceType | None = None
    version: int | None = None


class ProductPriceHistoryCreateSchema(ProductPriceHistoryBaseSchema):
    pass


class ProductPriceHistoryDBSchema(ProductPriceHistoryBaseSchema, BaseDBSchema):
    pass
