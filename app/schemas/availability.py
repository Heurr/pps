from uuid import UUID

from pydantic import Field

from app.constants import StockInfo
from app.schemas.base import BaseDBSchema, BaseIdModel, BaseMessageModel


class AvailabilityMessageSchema(BaseMessageModel):
    id: UUID = Field(..., alias="offerId")
    stock_info: StockInfo


class AvailabilityBaseSchema(BaseIdModel):
    in_stock: bool = False
    version: int


class AvailabilityUpdateSchema(BaseIdModel):
    in_stock: bool | None = None
    version: int | None = None


class AvailabilityCreateSchema(AvailabilityBaseSchema):
    pass


class AvailabilityDBSchema(AvailabilityBaseSchema, BaseDBSchema):
    pass
