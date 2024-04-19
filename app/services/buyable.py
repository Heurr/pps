from app.constants import Entity
from app.schemas.buyable import BuyableCreateSchema
from app.schemas.offer import OfferDBSchema
from app.services.simple_entity import SimpleEntityBaseService


class BuyableService(SimpleEntityBaseService[OfferDBSchema, BuyableCreateSchema]):
    def __init__(self):
        super().__init__(Entity.BUYABLE)
