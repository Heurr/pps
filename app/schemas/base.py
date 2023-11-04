from uuid import UUID

from pendulum import DateTime
from pydantic import BaseModel as _BaseModel

from app.constants import CountryCode


class BaseModel(_BaseModel):
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class BaseIdModel(BaseModel):
    id: UUID


class BaseMessageModel(BaseIdModel):
    version: int


class BaseDBSchema(BaseModel):
    created_at: DateTime
    updated_at: DateTime

    class Config:
        orm_mode = True


class BaseIdCountryModel(BaseIdModel):
    country_code: CountryCode


class DBBaseIdCountryModel(BaseIdCountryModel, BaseDBSchema):
    pass
