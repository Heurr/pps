from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, Field

from app.constants import Action, CountryCode
from app.exceptions import PriceServiceError


class BaseModel(_BaseModel):
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)


class EntityModel(BaseModel):
    id: UUID
    version: int
    country_code: CountryCode

    @property
    def version_column(self) -> str:
        """Override to return entity version column name in database"""
        return "version"

    def __ge__(self, other: EntityModel) -> bool:
        if hasattr(other, self.version_column):
            return self.version >= getattr(other, self.version_column)
        else:
            raise PriceServiceError(
                f"Not supported operation, {self.version_column} not found"
            )

    def __gt__(self, other: EntityModel) -> bool:
        if hasattr(other, self.version_column):
            return self.version > getattr(other, self.version_column)
        else:
            raise PriceServiceError(
                f"Not supported operation, {self.version_column} not found"
            )


class BaseDBSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class BaseRMQHeaders(BaseModel):
    user_agent: str = Field(alias="user-agent")
    content_type: str = Field(alias="content-type")
    hg_message_id: str = Field(
        alias="hg-message-id", default_factory=lambda: str(uuid4())
    )

    model_config = ConfigDict(populate_by_name=True)


class MessageModel(BaseModel):
    action: Action
    version: int


class EntityHeaders(BaseRMQHeaders):
    pass
