from uuid import UUID

from pydantic import Field

from app.constants import CountryCode, StockInfo
from app.schemas.base import BaseDBSchema, BaseModel, EntityModel, MessageModel


class AvailabilityLegacy(BaseModel):
    country_code: CountryCode = Field(alias="countryCode")


class Availability(BaseModel):
    stock_info: StockInfo = Field(alias="stockInfo")
    legacy: AvailabilityLegacy


class AvailabilityMessageSchema(MessageModel):
    """
    Docs: https://www.backstage.prod.heu.group/catalog/default/api/availability-async-api/definition
    """

    id: UUID = Field(alias="offerId")
    availability: Availability


class AvailabilityCreateSchema(EntityModel):
    in_stock: bool = False


class AvailabilityDBSchema(AvailabilityCreateSchema, BaseDBSchema):
    pass
