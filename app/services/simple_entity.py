from typing import Generic, TypeVar

from app.constants import Entity
from app.crud.base import DBSchemaTypeT
from app.crud.simple_entity import CreateSchemaTypeT, CRUDSimpleEntityBase
from app.services.base import BaseEntityService

UpdateCRUDTypeT = TypeVar("UpdateCRUDTypeT", bound=CRUDSimpleEntityBase)


class SimpleEntityBaseService(
    BaseEntityService[DBSchemaTypeT, CreateSchemaTypeT],
    Generic[DBSchemaTypeT, CreateSchemaTypeT],
):
    def __init__(
        self,
        entity: Entity,
    ):
        super().__init__(entity)

    def should_be_updated(
        self, obj_in: DBSchemaTypeT | None, msg_in: CreateSchemaTypeT
    ) -> bool:
        """When inserting one-column entity we ignore non-existent rows"""
        if obj_in is None:
            return False
        return super().should_be_updated(obj_in, msg_in)
