from datetime import datetime
from typing import Type
from uuid import UUID

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict

from app.constants import CountryCode
from app.exceptions import ApiError


class BaseModel(_BaseModel):
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class EntityModel(BaseModel):
    id: UUID
    version: int
    country_code: CountryCode

    def __ge__(self, other: Type["EntityModel"]) -> bool:
        if hasattr(other, "version"):
            return self.version >= other.version
        else:
            raise ApiError("Not supported operation, version not found")

    def __gt__(self, other: Type["EntityModel"]) -> bool:
        if hasattr(other, "version"):
            return self.version > other.version
        else:
            raise ApiError("Not supported operation, version not found")


class BaseDBSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    # TODO check if needed
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
