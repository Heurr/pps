from uuid import UUID

from pendulum import DateTime
from pydantic import Field

from app.constants import (
    LOCAL_PRODUCT_ID_STRING_LENGTH,
    CountryCode,
)

from .base import BaseModel


class ProductBaseSchema(BaseModel):
    id: UUID
    local_product_id: str = Field(..., max_length=LOCAL_PRODUCT_ID_STRING_LENGTH)
    name: str = Field(..., max_length=255)
    country: CountryCode
    version: int


class ProductCreateSchema(ProductBaseSchema):
    pass


class ProductUpdateSchema(BaseModel):
    id: UUID
    name: str | None = Field(None, max_length=255)
    version: int


class ProductBaseDBSchema(ProductBaseSchema):
    created_at: DateTime
    updated_at: DateTime

    class Config:
        orm_mode = True


class ProductDBSchema(ProductBaseDBSchema):
    pass
