import logging
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncConnection

from app.crud import CRUDBase
from app.db.tables.offer import offer_table
from app.db.tables.shop import shop_table
from app.schemas.offer import OfferDBSchema
from app.schemas.shop import ShopCreateSchema, ShopDBSchema

logger = logging.getLogger(__name__)


class CRUDShop(CRUDBase[ShopDBSchema, ShopCreateSchema]):
    def __init__(self):
        super().__init__(
            shop_table,
            ShopDBSchema,
            ["version", "certified", "verified", "paying", "enabled", "updated_at"],
        )

    async def get_offers_in_stock_for_shops(
        self, db_conn: AsyncConnection, shop_ids: list[UUID]
    ) -> list[OfferDBSchema]:
        """
        For each shop return all its offers which are in stock

        :param db_conn: Database connection
        :param shop_ids: List of shop UUIDs
        :return: List of offers
        """
        if not shop_ids:
            return []
        stmt = offer_table.select().where(
            and_(offer_table.c.shop_id.in_(shop_ids), offer_table.c.in_stock.is_(True))
        )
        res = await db_conn.execute(stmt)
        return [OfferDBSchema.model_validate(row) for row in res]


crud_shop = CRUDShop()
