from app.constants import CurrencyCode, ProductPriceType
from app.schemas.base import BaseIdCountryModel, BaseModel, DBBaseIdCountryModel


class ProductPriceBaseSchema(BaseModel):
    currency_code: CurrencyCode
    max_price: float
    min_price: float
    avg_price: float
    price_type: ProductPriceType
    version: int


class ProductPriceUpdateSchema(BaseIdCountryModel):
    currency_code: CurrencyCode | None = None
    max_price: float | None = None
    min_price: float | None = None
    avg_price: float | None = None
    price_type: ProductPriceType | None = None
    version: int | None = None


class ProductPriceCreateSchema(ProductPriceBaseSchema, BaseIdCountryModel):
    pass


class ProductPriceDBSchema(ProductPriceBaseSchema, DBBaseIdCountryModel):
    pass
