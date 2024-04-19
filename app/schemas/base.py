from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict

from app.constants import Action, CountryCode
from app.exceptions import PriceServiceError


class BaseModel(_BaseModel):
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))

    model_config = ConfigDict(arbitrary_types_allowed=True)


class EntityModel(BaseModel):
    id: UUID
    version: int
    country_code: CountryCode

    def __ge__(self, other: EntityModel) -> bool:
        if hasattr(other, "version"):
            return self.version >= other.version
        else:
            raise PriceServiceError("Not supported operation, version not found")

    def __gt__(self, other: EntityModel) -> bool:
        if hasattr(other, "version"):
            return self.version > other.version
        else:
            raise PriceServiceError("Not supported operation, version not found")


class BaseDBSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class MessageModel(BaseModel):
    action: Action
    version: int
