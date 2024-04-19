from uuid import UUID

from pydantic import Field, field_validator

from app.constants import CountryCode
from app.schemas.base import BaseDBSchema, BaseModel, EntityModel, MessageModel


class ShopState(BaseModel):
    verified: bool | None
    paying: bool | None
    enabled: bool | None


class ShopCertificate(BaseModel):
    enabled: bool | None


class ShopLegacy(BaseModel):
    country_code: CountryCode = Field(alias="countryCode")


class Shop(BaseModel):
    id: UUID
    legacy: ShopLegacy
    state: ShopState
    certificate: ShopCertificate


class ShopMessageSchema(MessageModel):
    """
    Docs: https://one-admin.gpages.heu.group/shop-entity-service/v1.5/api/index.html
    """

    shop: Shop


class ShopCreateSchema(EntityModel):
    certified: bool = False
    verified: bool = False
    paying: bool = False
    enabled: bool = False

    @field_validator("certified", "verified", "paying", "enabled", mode="before")
    @classmethod
    def convert_none_to_false(cls, value: bool | None) -> bool:
        return value if value else False


class ShopDBSchema(ShopCreateSchema, BaseDBSchema):
    pass
