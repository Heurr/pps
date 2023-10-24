from app.constants import CountryCode, CurrencyCode, ProductPriceType
from app.schemas.base import BaseDBSchema, BaseIdModel


class ProductDiscountBaseSchema(BaseIdModel):
    country_code: CountryCode
    currency_code: CurrencyCode
    discount: float
    price_type: ProductPriceType
    version: int


class ProductDiscountUpdateSchema(BaseIdModel):
    country_code: CountryCode | None = None
    currency_code: CurrencyCode | None = None
    discount: float | None = None
    price_type: ProductPriceType | None = None
    version: int | None = None


class ProductDiscountCreateSchema(ProductDiscountBaseSchema):
    pass


class ProductDiscountDBSchema(ProductDiscountBaseSchema, BaseDBSchema):
    pass
