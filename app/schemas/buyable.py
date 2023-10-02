from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseMessageModel


class BuyableMessageSchema(BaseMessageModel):
    offer_id: UUID = Field(..., alias="offerId")
    buyable: bool
