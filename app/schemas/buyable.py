from uuid import UUID

from pydantic import Field

from app.constants import CountryCode
from app.schemas.base import BaseDBSchema, BaseModel, EntityModel, MessageModel


class BuyableLegacy(BaseModel):
    country_code: CountryCode = Field(alias="countryCode")


class BuyableMessageSchema(MessageModel):
    """
    Docs: https://one-marketplace.gpages.heu.group/enablers/buyable-service/buyable/
    """

    buyable: bool
    id: UUID = Field(alias="offerId")
    legacy: BuyableLegacy


class BuyableCreateSchema(EntityModel):
    buyable: bool = False


class BuyableDBSchema(BuyableCreateSchema, BaseDBSchema):
    pass
