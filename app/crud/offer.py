import logging
from typing import Type
from uuid import UUID

from sqlalchemy import Table, bindparam, text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.crud.base import CRUDBase
from app.db.tables.offer import offer_table
from app.schemas.offer import OfferCreateSchema, OfferDBSchema

logger = logging.getLogger(__name__)


class CRUDOffer(CRUDBase[OfferDBSchema, OfferCreateSchema]):
    def __init__(
        self,
        table: Table,
        db_scheme: Type[OfferDBSchema],
        create_scheme: Type[OfferCreateSchema],
    ):
        super().__init__(
            table,
            db_scheme,
            create_scheme,
            ["version", "product_id", "shop_id", "price", "currency_code", "updated_at"],
        )

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


crud_offer = CRUDOffer(
    table=offer_table,
    db_scheme=OfferDBSchema,
    create_scheme=OfferCreateSchema,
)
