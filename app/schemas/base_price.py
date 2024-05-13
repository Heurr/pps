from uuid import UUID

from app.constants import ProductPriceType
from app.schemas.base import BaseDBSchema, BaseModel


class BasePriceCreateSchema(BaseModel):
    product_id: UUID
    price_type: ProductPriceType
    price: float


class BasePriceDBSchema(BasePriceCreateSchema, BaseDBSchema):
    pass
