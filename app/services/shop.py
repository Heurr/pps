from app.constants import Entity
from app.schemas.shop import (
    ShopCreateSchema,
    ShopDBSchema,
)
from app.services.base import BaseEntityService


class ShopService(BaseEntityService[ShopDBSchema, ShopCreateSchema]):
    def __init__(self):
        super().__init__(Entity.SHOP)
