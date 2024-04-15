from app.constants import StockInfo
from app.schemas.base import BaseDBSchema, EntityModel


class AvailabilityMessageSchema(EntityModel):
    stock_info: StockInfo


class AvailabilityCreateSchema(EntityModel):
    in_stock: bool = False


class AvailabilityUpdateSchema(EntityModel):
    in_stock: bool | None = None


class AvailabilityDBSchema(AvailabilityCreateSchema, BaseDBSchema):
    pass
