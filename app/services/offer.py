from app.constants import Entity
from app.schemas.offer import (
    OfferCreateSchema,
    OfferDBSchema,
)
from app.services.base import BaseEntityService


class OfferService(BaseEntityService[OfferDBSchema, OfferCreateSchema]):
    def __init__(self):
        super().__init__(Entity.OFFER)
