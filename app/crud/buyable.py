from app.constants import Entity
from app.crud.simple_entity import CRUDSimpleEntityBase
from app.db.tables.offer import offer_table
from app.schemas.buyable import BuyableCreateSchema
from app.schemas.offer import OfferDBSchema


class CRUDBuyable(CRUDSimpleEntityBase[OfferDBSchema, BuyableCreateSchema]):
    def __init__(self):
        super().__init__(offer_table, OfferDBSchema, Entity.BUYABLE)


crud_buyable = CRUDBuyable()
