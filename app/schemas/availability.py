from uuid import UUID

from pydantic import Field

from app.constants import StockInfo
from app.schemas.base import BaseMessageModel


class AvailabilityMessageSchema(BaseMessageModel):
    id: UUID = Field(..., alias="offerId")
    stock_info: StockInfo
