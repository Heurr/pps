import logging

from app.db.tables.shop import shop_table
from app.schemas.shop import ShopCreateSchema, ShopDBSchema

from .base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDShop(CRUDBase[ShopDBSchema, ShopCreateSchema]):
    def __init__(self):
        super().__init__(
            shop_table,
            ShopDBSchema,
            ["version", "certified", "verified", "paying", "enabled", "updated_at"],
        )


crud_shop = CRUDShop()
