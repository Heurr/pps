from app.crud.simple_entity import CRUDSimpleEntityBase
from app.db.tables.offer import offer_table
from app.schemas.availability import (
    AvailabilityCreateSchema,
)
from app.schemas.offer import OfferDBSchema


class CRUDAvailability(CRUDSimpleEntityBase[OfferDBSchema, AvailabilityCreateSchema]):
    def __init__(self):
        super().__init__(
            offer_table,
            OfferDBSchema,
            AvailabilityCreateSchema,
            "in_stock",
            "availability_version",
        )


crud_availability = CRUDAvailability()
