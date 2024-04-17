from app.constants import Entity
from app.crud.shop import CRUDShop, crud_shop
from app.schemas.shop import (
    ShopCreateSchema,
    ShopDBSchema,
)
from app.services.base import BaseMessageService


class ShopService(BaseMessageService[CRUDShop, ShopDBSchema, ShopCreateSchema]):
    def __init__(self):
        super().__init__(crud_shop, Entity.SHOP, ShopCreateSchema)
