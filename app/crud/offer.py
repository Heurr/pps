import logging
from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import bindparam, text, tuple_
from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import (
    ENTITY_VERSION_COLUMNS,
    Aggregate,
    Entity,
    ProductPriceType,
)
from app.crud.base import CRUDBase
from app.custom_types import OfferPk
from app.db.tables.offer import offer_table
from app.schemas.offer import OfferCreateSchema, OfferDBSchema, PopulationOfferSchema

logger = logging.getLogger(__name__)


class CRUDOffer(CRUDBase[OfferDBSchema, OfferCreateSchema]):
    def __init__(self):
        super().__init__(
            offer_table,
            OfferDBSchema,
            ["version", "product_id", "shop_id", "price", "currency_code", "updated_at"],
        )

    SQL_FILTERS = {
        ProductPriceType.MARKETPLACE: "offers.buyable = TRUE",
        ProductPriceType.IN_STOCK_CERTIFIED: "shops.certified = TRUE AND offers.in_stock = TRUE",
        ProductPriceType.IN_STOCK: "offers.in_stock = TRUE",
    }

    async def get_in(
        self, db_conn: AsyncConnection, obj_ids: list[UUID]
    ) -> list[OfferDBSchema]:
        stmt = text(
            """
            SELECT offers.*, shops.certified AS certified_shop
            FROM offers
            LEFT JOIN shops ON shops.id = offers.shop_id
            WHERE offers.id IN :ids
        """
        ).bindparams(bindparam("ids", value=obj_ids, expanding=True))
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.model_validate(row) for row in rows]

    async def get_unpopulated_offers(
        self, db_conn: AsyncConnection, batch_size: int
    ) -> AsyncGenerator[list[PopulationOfferSchema], None]:
        """
        Get all offers which have either entity version set to -1. Return results
        in batches of size `batch_size`.

        All entities are queried at once because this we save db operations if we do
        it one big query with batches
        """
        stmt = (
            text(
                """
            SELECT offers.id, offers.product_id, offers.created_at, offers.in_stock, offers.buyable,
            offers.availability_version, offers.buyable_version
            FROM offers
            WHERE offers.buyable_version = :version or offers.availability_version = :version
            """
            )
            .bindparams(version=-1)
            .execution_options(yield_per=batch_size)
        )
        async with db_conn.stream(stmt) as res:
            async for batch in res.mappings().partitions(batch_size):
                yield [PopulationOfferSchema.model_validate(row) for row in batch]

    async def set_offers_as_populated(
        self, db_conn: AsyncConnection, entities: list[Entity], pks: list[OfferPk]
    ) -> None:
        """
        Set offers as populated for given entities by setting their version to 0.
        """
        stmt = (
            self.table.update()
            .where(tuple_(self.table.c.product_id, self.table.c.id).in_(pks))
            .values({ENTITY_VERSION_COLUMNS[entity]: 0 for entity in entities})
        )
        await db_conn.execute(stmt)

    async def get_price_for_product(
        self,
        db_conn: AsyncConnection,
        product_id: UUID,
        price_type: ProductPriceType,
        aggregate: Aggregate,
    ) -> float | None:
        sql_filter = self.SQL_FILTERS.get(price_type)
        additional_condition = f"AND {sql_filter}" if sql_filter else ""
        additional_join = (
            "LEFT JOIN shops ON shops.id = offers.shop_id"
            if price_type == ProductPriceType.IN_STOCK_CERTIFIED
            else ""
        )

        stmt = text(
            f"""
            SELECT {aggregate}(offers.price)
            FROM offers
            {additional_join}
            WHERE offers.product_id = :product_id
            {additional_condition}
            """
        ).bindparams(bindparam("product_id", value=product_id))

        row = await db_conn.execute(stmt)
        return row.first()[0]  # type: ignore


crud_offer = CRUDOffer()
