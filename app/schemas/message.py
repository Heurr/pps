from pydantic import ConfigDict

from app.constants import Entity
from app.schemas.base import BaseModel


class InvalidMessageSchema(BaseModel):
    entity: Entity
    msg: str


class MessageSchema(BaseModel):
    country_code: str | None = None
    action: str
    entity: Entity
    msg: str | None = None

    model_config = ConfigDict(coerce_numbers_to_str=True)
