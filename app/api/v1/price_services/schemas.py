from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class PriceServiceRequest(BaseModel):
    product_id: UUID = Field(..., description="One Platform product ID")


class PriceServiceResponse(BaseModel):
    product_name: str = Field(..., description="Product name", example="datart")
    product_local_id: str = Field(..., description="Legacy product ID", example="2131")
