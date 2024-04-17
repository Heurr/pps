import logging
from typing import Type

from sqlalchemy import Table

from app.db.tables.shop import shop_table
from app.schemas.shop import ShopCreateSchema, ShopDBSchema

from .base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDShop(CRUDBase[ShopDBSchema, ShopCreateSchema]):
    def __init__(
        self,
        table: Table,
        db_scheme: Type[ShopDBSchema],
        create_scheme: Type[ShopCreateSchema],
    ):
        super().__init__(
            table,
            db_scheme,
            create_scheme,
            ["version", "certified", "verified", "paying", "enabled", "updated_at"],
        )


crud_shop = CRUDShop(
    table=shop_table,
    db_scheme=ShopDBSchema,
    create_scheme=ShopCreateSchema,
)
