from datetime import datetime
from uuid import UUID

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict

from app.constants import CountryCode


class BaseModel(_BaseModel):
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class BaseIdModel(BaseModel):
    id: UUID


class BaseMessageModel(BaseIdModel):
    version: int


class BaseDBSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    # TODO check if needed
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class BaseIdCountryModel(BaseIdModel):
    country_code: CountryCode


class DBBaseIdCountryModel(BaseIdCountryModel, BaseDBSchema):
    pass
