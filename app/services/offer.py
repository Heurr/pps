from app.constants import Entity
from app.crud.offer import CRUDOffer, crud_offer
from app.schemas.offer import (
    OfferCreateSchema,
    OfferDBSchema,
)
from app.services.base import BaseEntityService


class OfferService(BaseEntityService[CRUDOffer, OfferDBSchema, OfferCreateSchema]):
    def __init__(self):
        super().__init__(crud_offer, Entity.OFFER, OfferCreateSchema)
