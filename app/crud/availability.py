from typing import Type

from sqlalchemy import Table

from app.crud.base import CRUDBase
from app.db.tables.availability import availability_table
from app.schemas.availability import (
    AvailabilityCreateSchema,
    AvailabilityDBSchema,
)


class CRUDAvailability(CRUDBase[AvailabilityDBSchema, AvailabilityCreateSchema]):
    def __init__(
        self,
        table: Table,
        db_scheme: Type[AvailabilityDBSchema],
        create_scheme: Type[AvailabilityCreateSchema],
    ):
        super().__init__(
            table,
            db_scheme,
            create_scheme,
            ["version", "in_stock", "updated_at"],
        )


crud_availability = CRUDAvailability(
    table=availability_table,
    db_scheme=AvailabilityDBSchema,
    create_scheme=AvailabilityCreateSchema,
)
