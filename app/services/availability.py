from app.constants import Entity
from app.schemas.availability import AvailabilityCreateSchema
from app.schemas.offer import OfferDBSchema
from app.services.simple_entity import SimpleEntityBaseService


class AvailabilityService(
    SimpleEntityBaseService[OfferDBSchema, AvailabilityCreateSchema]
):
    def __init__(self):
        super().__init__(Entity.AVAILABILITY)
