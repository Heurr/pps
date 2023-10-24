from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseDBSchema, BaseIdModel, BaseMessageModel


class BuyableMessageSchema(BaseMessageModel):
    offer_id: UUID = Field(..., alias="offerId")
    buyable: bool


class BuyableBaseSchema(BaseIdModel):
    buyable: bool = False
    version: int


class BuyableUpdateSchema(BaseIdModel):
    buyable: bool | None = None
    version: int | None = None


class BuyableCreateSchema(BuyableBaseSchema):
    pass


class BuyableDBSchema(BuyableBaseSchema, BaseDBSchema):
    pass
