from app.constants import Entity
from app.crud.availability import CRUDAvailability, crud_availability
from app.schemas.availability import (
    AvailabilityCreateSchema,
    AvailabilityDBSchema,
)
from app.services.base import BaseMessageService


class AvailabilityService(
    BaseMessageService[
        CRUDAvailability,
        AvailabilityDBSchema,
        AvailabilityCreateSchema,
    ]
):
    def __init__(self):
        super().__init__(
            crud_availability,
            Entity.AVAILABILITY,
            AvailabilityCreateSchema,
        )
