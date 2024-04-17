from app.constants import Entity
from app.crud.buyable import CRUDBuyable, crud_buyable
from app.schemas.buyable import BuyableCreateSchema, BuyableDBSchema
from app.services.base import BaseMessageService


class BuyableService(
    BaseMessageService[
        CRUDBuyable,
        BuyableDBSchema,
        BuyableCreateSchema,
    ]
):
    def __init__(self):
        super().__init__(crud_buyable, Entity.BUYABLE, BuyableCreateSchema)
