from app.constants import ProductPriceType
from app.schemas.base import BaseIdCountryModel, BaseModel, DBBaseIdCountryModel


class ProductDiscountBaseSchema(BaseModel):
    discount: float
    price_type: ProductPriceType
    version: int


class ProductDiscountUpdateSchema(BaseIdCountryModel):
    discount: float | None = None
    price_type: ProductPriceType | None = None
    version: int | None = None


class ProductDiscountCreateSchema(ProductDiscountBaseSchema, BaseIdCountryModel):
    pass


class ProductDiscountDBSchema(ProductDiscountBaseSchema, DBBaseIdCountryModel):
    pass
