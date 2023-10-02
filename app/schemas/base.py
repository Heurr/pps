from uuid import UUID

from pydantic import BaseModel as _BaseModel


class BaseModel(_BaseModel):
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class BaseIdModel(BaseModel):
    id: UUID


class BaseMessageModel(BaseIdModel):
    version: int
