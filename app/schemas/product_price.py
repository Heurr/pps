from app.constants import CountryCode, CurrencyCode, ProductPriceType
from app.schemas.base import BaseDBSchema, BaseIdModel


class ProductPriceBaseSchema(BaseIdModel):
    country_code: CountryCode
    currency_code: CurrencyCode
    max_price: float
    min_price: float
    avg_price: float
    price_type: ProductPriceType
    version: int


class ProductPriceUpdateSchema(BaseIdModel):
    country_code: CountryCode | None = None
    currency_code: CurrencyCode | None = None
    max_price: float | None = None
    min_price: float | None = None
    avg_price: float | None = None
    price_type: ProductPriceType | None = None
    version: int | None = None


class ProductPriceCreateSchema(ProductPriceBaseSchema):
    pass


class ProductPriceDBSchema(ProductPriceBaseSchema, BaseDBSchema):
    pass
