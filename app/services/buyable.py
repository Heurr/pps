from app.constants import Entity
from app.crud.buyable import CRUDBuyable, crud_buyable
from app.schemas.buyable import BuyableCreateSchema, BuyableDBSchema
from app.services.base import BaseEntityService


class BuyableService(
    BaseEntityService[
        CRUDBuyable,
        BuyableDBSchema,
        BuyableCreateSchema,
    ]
):
    def __init__(self):
        super().__init__(crud_buyable, Entity.BUYABLE, BuyableCreateSchema)
